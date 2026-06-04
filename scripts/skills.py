#!/usr/bin/env python3
"""Upstream skill routing and safety audit for econ-paper-studio."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = PROJECT_ROOT / "research_skill_registry.yaml"
TEXT_SUFFIXES = {".md", ".py", ".sh", ".ps1", ".js", ".ts", ".yaml", ".yml", ".json", ".txt"}


@dataclass
class SkillEntry:
    name: str
    source: str
    role: str


@dataclass
class PhaseEntry:
    name: str
    description: str
    skill_names: list[str]


@dataclass
class SkillRegistry:
    version: int
    purpose: str
    external_reference_policy: dict[str, Any]
    skills: list[SkillEntry]
    phases: dict[str, PhaseEntry]
    tasks: dict[str, list[str]]


@dataclass
class SkillPlanStep:
    phase: str
    description: str
    skill_names: list[str]
    sources: list[str]


@dataclass
class SkillPlan:
    task: str
    external_reference_policy: dict[str, Any]
    steps: list[SkillPlanStep]


@dataclass
class SkillAuditCheck:
    id: str
    title: str
    severity: str
    passed: bool
    evidence: str
    recommendation: str


@dataclass
class SkillAuditResult:
    path: str
    risk_level: str
    checks: list[SkillAuditCheck]


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> SkillRegistry:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    skills = [
        SkillEntry(name=str(item["name"]), source=str(item["source"]), role=str(item.get("role", "")))
        for item in raw.get("skills", [])
    ]
    phases = {
        name: PhaseEntry(
            name=name,
            description=str(value.get("description", "")),
            skill_names=_list(value.get("skills")),
        )
        for name, value in (raw.get("phases") or {}).items()
    }
    tasks = {name: _list(value.get("phases")) for name, value in (raw.get("tasks") or {}).items()}
    return SkillRegistry(
        version=int(raw.get("version", 1)),
        purpose=str(raw.get("purpose", "")),
        external_reference_policy=dict(raw.get("external_reference_policy") or {}),
        skills=skills,
        phases=phases,
        tasks=tasks,
    )


def plan_task(registry: SkillRegistry, task: str) -> SkillPlan:
    if task not in registry.tasks:
        known = ", ".join(sorted(registry.tasks))
        raise ValueError(f"unknown task `{task}`; known tasks: {known}")
    source_by_name = {item.name: item.source for item in registry.skills}
    steps: list[SkillPlanStep] = []
    for phase_name in registry.tasks[task]:
        phase = registry.phases[phase_name]
        steps.append(
            SkillPlanStep(
                phase=phase.name,
                description=phase.description,
                skill_names=phase.skill_names,
                sources=[source_by_name.get(name, "local-or-user-provided") for name in phase.skill_names],
            )
        )
    return SkillPlan(task=task, external_reference_policy=registry.external_reference_policy, steps=steps)


def _check(check_id: str, title: str, severity: str, passed: bool, evidence: str, recommendation: str) -> SkillAuditCheck:
    return SkillAuditCheck(check_id, title, severity, passed, evidence, recommendation)


def _collect_text(path: Path) -> str:
    chunks: list[str] = []
    if not path.exists():
        return ""
    for item in path.rglob("*"):
        if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES:
            try:
                chunks.append(item.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    return "\n".join(chunks)


def _has_any(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(0)[:120]
    return None


def audit_skill_dir(path: str | Path) -> SkillAuditResult:
    root = Path(path)
    text = _collect_text(root)
    checks = [
        _check(
            "skill_md.present",
            "SKILL.md is present",
            "high",
            (root / "SKILL.md").exists(),
            str(root / "SKILL.md"),
            "Read and inspect a top-level SKILL.md before asking an agent to load this skill.",
        )
    ]
    risk_patterns = [
        (
            "risk.env_access",
            "Environment or secret access",
            [r"os\.environ", r"getenv\s*\(", r"API[_-]?KEY", r"SECRET", r"TOKEN"],
            "Review why the skill reads environment variables or secrets before installing it.",
        ),
        (
            "risk.network_call",
            "Network calls or remote downloads",
            [r"requests\.", r"urllib\.", r"https?://", r"\bcurl\b", r"\bwget\b"],
            "Confirm every network destination and disable unexpected uploads/downloads.",
        ),
        (
            "risk.ssh_or_key",
            "SSH keys or credential files",
            [r"\.ssh", r"id_rsa", r"private[_-]?key", r"authorized_keys"],
            "Do not load a skill that reads SSH keys or credential files without review.",
        ),
        (
            "risk.browser_data",
            "Browser or local profile data",
            [r"Chrome", r"Cookies", r"Login Data", r"browser"],
            "Check whether browser/profile access is required and safe for the task.",
        ),
    ]
    for check_id, title, patterns, recommendation in risk_patterns:
        hit = _has_any(text, patterns)
        checks.append(
            _check(
                check_id,
                title,
                "high",
                hit is None,
                hit or "No matching risky pattern found.",
                recommendation,
            )
        )
    risk_level = "high" if any(check.severity == "high" and not check.passed for check in checks) else "low"
    return SkillAuditResult(path=str(root), risk_level=risk_level, checks=checks)


def render_plan(plan: SkillPlan) -> str:
    lines = [
        "# Skill Load Plan",
        "",
        f"- Task: `{plan.task}`",
        f"- Install outside repo: `{plan.external_reference_policy.get('install_outside_repo', True)}`",
        "",
        "## Ordered Phases",
        "",
    ]
    for index, step in enumerate(plan.steps, start=1):
        lines.append(f"### {index}. {step.phase}")
        lines.append("")
        lines.append(step.description)
        lines.append("")
        for name, source in zip(step.skill_names, step.sources, strict=False):
            lines.append(f"- {name}: {source}")
        lines.append("")
    lines.extend(
        [
            "## Use Boundary",
            "",
            "Do not copy upstream repositories into this project. Install or mount them in the agent skill directory, read each SKILL.md before use, and record the source URL plus commit when a real paper task uses them.",
        ]
    )
    return "\n".join(lines)


def render_audit(result: SkillAuditResult) -> str:
    lines = [
        "# Skill Safety Audit",
        "",
        f"- Path: `{result.path}`",
        f"- Risk level: **{result.risk_level}**",
        "",
        "| Status | Severity | Check | Evidence |",
        "|---|---|---|---|",
    ]
    for check in result.checks:
        status = "[PASS]" if check.passed else "[FAIL]"
        lines.append(f"| {status} | {check.severity} | {check.title} | {check.evidence.replace(chr(10), ' ')} |")
    failed = [check for check in result.checks if not check.passed]
    lines.extend(["", "## Next Actions", ""])
    if failed:
        lines.extend(f"- [{check.severity}] {check.recommendation}" for check in failed)
    else:
        lines.append("- No obvious local skill safety issue found. Still review upstream code and license before use.")
    return "\n".join(lines)


def _print_text(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan and audit upstream skills for econ-paper-studio.")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="Plan which skills to load for a research task")
    plan_parser.add_argument("--task", required=True, help="Task name, for example full-paper")
    plan_parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Registry YAML path")
    plan_parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")

    audit_parser = sub.add_parser("audit", help="Audit a local upstream skill directory")
    audit_parser.add_argument("--dir", required=True, help="Skill directory to inspect")
    audit_parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")

    args = parser.parse_args()
    if args.command == "plan":
        try:
            plan = plan_task(load_registry(args.registry), args.task)
        except ValueError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 2
        text = json.dumps(asdict(plan), ensure_ascii=False, indent=2) if args.json else render_plan(plan)
        _print_text(text)
        return 0
    if args.command == "audit":
        result = audit_skill_dir(args.dir)
        text = json.dumps(asdict(result), ensure_ascii=False, indent=2) if args.json else render_audit(result)
        _print_text(text)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
