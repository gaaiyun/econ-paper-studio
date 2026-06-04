#!/usr/bin/env python3
"""Paper outline and quality audit tools for econ-paper-studio."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from robustness_checks import (
    CheckResult,
    scan_anti_ai_phrases,
    scan_causal_overclaims,
    scan_citation_risks,
)


@dataclass
class PaperAuditResult:
    paper_path: str
    score: float
    checks: list[CheckResult]


def _severity_weight(severity: str) -> int:
    return {"critical": 3, "high": 2, "medium": 1}.get(severity, 1)


def _score_checks(checks: list[CheckResult]) -> float:
    total = sum(_severity_weight(item.severity) for item in checks) or 1
    passed = sum(_severity_weight(item.severity) for item in checks if item.passed)
    return round(10 * passed / total, 1)


def _check(check_id: str, title: str, severity: str, passed: bool, evidence: str, recommendation: str) -> CheckResult:
    return CheckResult(
        id=check_id,
        title=title,
        severity=severity,
        passed=passed,
        evidence=evidence,
        recommendation=recommendation,
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _has_heading(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def _section_check(text: str) -> CheckResult:
    sections = {
        "introduction": [r"^\s*#+\s*(introduction|引言|导论)\b"],
        "data": [r"^\s*#+\s*(data|sample|数据|样本)\b"],
        "empirical strategy": [r"^\s*#+\s*(empirical strategy|method|methodology|识别|方法|模型)\b"],
        "results": [r"^\s*#+\s*(results|findings|结果|实证结果)\b"],
        "robustness": [r"^\s*#+\s*(robustness|sensitivity|稳健性|敏感性)\b"],
        "references": [r"^\s*#+\s*(references|bibliography|参考文献)\b"],
    }
    missing = [name for name, patterns in sections.items() if not _has_heading(text, patterns)]
    return _check(
        "paper.core_sections",
        "Core paper sections are present",
        "critical",
        not missing,
        "missing: " + ", ".join(missing) if missing else "all core sections found",
        "Add the missing paper sections before treating the draft as submission-ready.",
    )


def _contribution_check(text: str) -> CheckResult:
    patterns = [
        r"\bcentral contribution\b",
        r"\bmain contribution\b",
        r"\bthis paper contributes\b",
        r"\bour contribution\b",
        r"本文(的)?(核心|主要)?贡献",
        r"本文贡献在于",
    ]
    matched = None
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            matched = match.group(0)
            break
    return _check(
        "paper.contribution_sentence",
        "One-sentence contribution is explicit",
        "high",
        matched is not None,
        matched or "no contribution sentence marker found",
        "State the paper's contribution in one concrete sentence before expanding the introduction.",
    )


def _caption_lines(text: str) -> list[str]:
    captions: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^(table|figure)\s+\d+[\.:：\-\s]", stripped, flags=re.IGNORECASE) or re.match(
            r"^[表图]\s*\d+[\.:：\-\s]", stripped
        ):
            captions.append(stripped)
    return captions


def _word_count(text: str) -> int:
    latin = re.findall(r"[A-Za-z0-9]+", text)
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    return len(latin) + max(0, len(cjk) // 2)


def _caption_check(text: str) -> CheckResult:
    captions = _caption_lines(text)
    if not captions:
        return _check(
            "caption.quality",
            "Figure and table captions are review-ready",
            "medium",
            False,
            "no table or figure captions found",
            "Add captions that state the estimand, sample, period, uncertainty display, or clustering level.",
        )

    weak = [caption for caption in captions if _word_count(caption) < 10 or re.search(r"\b(results?|plot|figure|table)\b$", caption, flags=re.IGNORECASE)]
    return _check(
        "caption.quality",
        "Figure and table captions are review-ready",
        "medium",
        not weak,
        f"{len(captions)} captions checked; weak: {weak[:3]}" if weak else f"{len(captions)} captions checked",
        "Rewrite short captions so readers know what is estimated, on which sample, and with what uncertainty.",
    )


def audit_paper(paper_path: str | Path) -> PaperAuditResult:
    path = Path(paper_path)
    checks: list[CheckResult] = [
        _check(
            "paper.exists",
            "Paper file exists",
            "critical",
            path.exists(),
            str(path),
            "Point the audit to an existing Markdown, LaTeX, or text draft.",
        )
    ]

    if not path.exists():
        return PaperAuditResult(paper_path=str(path), score=_score_checks(checks), checks=checks)

    text = _read_text(path)
    checks.append(_section_check(text))
    checks.append(_contribution_check(text))
    checks.append(_caption_check(text))
    checks.extend(scan_anti_ai_phrases([path]))
    checks.extend(scan_citation_risks([path]))
    checks.extend(scan_causal_overclaims([path]))

    return PaperAuditResult(paper_path=str(path), score=_score_checks(checks), checks=checks)


def render_audit(result: PaperAuditResult) -> str:
    passed = sum(1 for item in result.checks if item.passed)
    failed = len(result.checks) - passed
    lines = [
        "# Paper Quality Audit",
        "",
        f"- Paper: `{result.paper_path}`",
        f"- Score: **{result.score:.1f} / 10**",
        f"- Checks: {passed} passed, {failed} failed",
        "",
        "## Checks",
        "",
        "| Status | Severity | Check | Evidence |",
        "|---|---|---|---|",
    ]
    for check in result.checks:
        status = "[PASS]" if check.passed else "[FAIL]"
        evidence = check.evidence.replace("\n", " ")[:160]
        lines.append(f"| {status} | {check.severity} | {check.title} | {evidence} |")

    failed_checks = [item for item in result.checks if not item.passed]
    lines.extend(["", "## Next Actions", ""])
    if failed_checks:
        for check in failed_checks:
            lines.append(f"- [{check.severity}] {check.recommendation}")
    else:
        lines.append("- No blocking paper-audit issues found. Still verify each source and numerical result manually.")

    lines.extend(
        [
            "",
            "## Scope Note",
            "",
            "This audit checks structure, obvious citation placeholders, causal overclaim risk, filler phrases, and caption discipline. It does not verify that cited sources exist or that references support the claims.",
        ]
    )
    return "\n".join(lines)


def _value(data: dict[str, Any], key: str, default: str = "[待填写]") -> str:
    value = data.get(key)
    if value is None or value == "":
        return default
    return str(value).strip()


def render_outline(brief: dict[str, Any]) -> str:
    question = _value(brief, "question")
    contribution = _value(brief, "contribution")
    strategy = _value(brief, "identification_seed", "unspecified")
    target = _value(brief, "target_journal", "field journal")
    data = brief.get("data") if isinstance(brief.get("data"), dict) else {}
    unit_id = _value(data, "unit_id") if isinstance(data, dict) else "[待填写]"
    time_id = _value(data, "time_id") if isinstance(data, dict) else "[待填写]"
    outcome = _value(data, "outcome") if isinstance(data, dict) else "[待填写]"

    return "\n".join(
        [
            "# Paper Outline",
            "",
            f"- Research question: {question}",
            f"- Target outlet: {target}",
            f"- Identification seed: {strategy}",
            f"- One-sentence contribution: {contribution}",
            "",
            "## Abstract",
            "",
            "- Problem: [待填写，用一到两句说明研究对象和政策背景]",
            f"- Design: {strategy}; unit `{unit_id}`, time `{time_id}`, outcome `{outcome}`",
            "- Evidence: [待填写主估计、置信区间、样本范围；不得编造数值]",
            "- Interpretation boundary: [待填写识别假设和主要限制]",
            "",
            "## Introduction",
            "",
            "- Opening fact: [待核验来源] 写一个可查证的制度事实或数据事实。",
            "- Gap: 说明现有文献没有解决的识别、样本或机制问题。",
            "- Contribution sentence: 保留一条具体贡献句，不使用泛泛的贡献清单。",
            "- Roadmap: 用研究设计、结果、稳健性和机制顺序组织。",
            "",
            "## Data And Sample",
            "",
            "- Data source: [待核验来源] 写清来源、年份、口径、下载或构造路径。",
            "- Sample construction: 记录删样规则、合并键、缺失处理和样本量变化。",
            "- Variables: 列出 outcome、treatment、controls、cluster 口径。",
            "",
            "## Empirical Strategy",
            "",
            f"- Baseline model: 写出 {strategy} 的方程和估计量。",
            "- Identification: 写明核心假设和可检验诊断，不把稳健性写成证明。",
            "- Inference: 明确聚类层级、小样本校正和多重检验处理。",
            "",
            "## Results",
            "",
            "- Baseline table: 报告系数、标准误/置信区间、样本量、固定效应和聚类层级。",
            "- Economic magnitude: 把系数翻译成可解释量级，避免只讨论显著性。",
            "- Figure/table captions: 每个标题说明估计对象、样本、时间范围和不确定性。",
            "",
            "## Robustness And Validity",
            "",
            "- Identification diagnostics: 平行趋势、placebo、bandwidth、first-stage 或对应方法诊断。",
            "- Alternative specifications: 控制变量、样本、权重、聚类、估计器替代。",
            "- Multiple testing: 多结果或多异质性时说明校正方案。",
            "",
            "## Mechanisms, Heterogeneity, And Limits",
            "",
            "- Mechanism: 只写数据中实际能支持的机制，不扩展到未检验渠道。",
            "- Heterogeneity: 预先说明分组依据和多重检验边界。",
            "- Limitations: 写清外部有效性、识别假设和测量误差。",
            "",
            "## References",
            "",
            "- 每条引用必须能在 Crossref/OpenAlex/Semantic Scholar、期刊官网或 DOI 页面核验。",
            "- 不保留作者年份占位符、citation-needed 标记、未知 DOI 或未读文献。",
        ]
    )


def _load_brief(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("brief must be a mapping")
    return data


def _print_text(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Paper outline and writing-quality tools.")
    sub = parser.add_subparsers(dest="command", required=True)

    audit_parser = sub.add_parser("audit", help="Audit a paper draft")
    audit_parser.add_argument("--paper", required=True, help="Markdown/LaTeX/text draft to audit")
    audit_parser.add_argument("--output", help="Write Markdown or JSON report")
    audit_parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    audit_parser.add_argument("--fail-under", type=float, default=None, help="Return exit code 2 if score is below this threshold")

    outline_parser = sub.add_parser("outline", help="Render a paper outline from a research brief")
    outline_parser.add_argument("--brief", required=True, help="YAML research brief")
    outline_parser.add_argument("--output", help="Write Markdown outline to this path")

    args = parser.parse_args()

    if args.command == "audit":
        result = audit_paper(args.paper)
        text = json.dumps(asdict(result), ensure_ascii=False, indent=2) if args.json else render_audit(result)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
        _print_text(text)
        if args.fail_under is not None and result.score < args.fail_under:
            print(f"[error] Paper audit score {result.score:.1f} below threshold {args.fail_under:.1f}", file=sys.stderr)
            return 2
        return 0

    if args.command == "outline":
        text = render_outline(_load_brief(Path(args.brief)))
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
        _print_text(text)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
