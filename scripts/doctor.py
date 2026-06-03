#!/usr/bin/env python3
"""Local health checks for econ-paper-studio."""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path

REQUIRED_FILES = [
    "README.md",
    "INSTALL_CN.md",
    "PROJECT_PLAN.md",
    "WORKFLOW.md",
    "RESEARCH_QUESTION.md",
    "SKILL.md",
    "pyproject.toml",
    "scripts/cli.py",
    "scripts/identify_strategy.py",
    "scripts/scaffold.py",
    "scripts/robustness_checks.py",
    "scripts/session.py",
    "examples/case-min-wage-did/research_brief.yaml",
]

REQUIRED_IMPORTS = ["yaml"]
OPTIONAL_IMPORTS = ["statspai", "pandas", "numpy", "scipy", "rich"]


def _check(check_id: str, title: str, passed: bool, detail: str) -> dict:
    return {
        "id": check_id,
        "title": title,
        "passed": passed,
        "detail": detail,
    }


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_checks(project_root: Path | None = None) -> dict:
    root = project_root or Path(__file__).resolve().parent.parent
    checks: list[dict] = []

    py_ok = sys.version_info >= (3, 10)
    checks.append(
        _check(
            "python.version",
            "Python >= 3.10",
            py_ok,
            platform.python_version(),
        )
    )

    for rel in REQUIRED_FILES:
        path = root / rel
        checks.append(
            _check(
                f"file.{rel}",
                f"Required file: {rel}",
                path.exists(),
                str(path),
            )
        )

    for name in REQUIRED_IMPORTS:
        checks.append(
            _check(
                f"import.{name}",
                f"Required import: {name}",
                _module_available(name),
                "available" if _module_available(name) else "missing",
            )
        )

    for name in OPTIONAL_IMPORTS:
        checks.append(
            _check(
                f"optional.{name}",
                f"Optional import: {name}",
                _module_available(name),
                "available" if _module_available(name) else "missing",
            )
        )

    passed = sum(1 for item in checks if item["passed"])
    failed = len(checks) - passed
    return {
        "project_root": str(root),
        "python_version": platform.python_version(),
        "passed": passed,
        "failed": failed,
        "checks": checks,
    }


def render_text(result: dict) -> str:
    lines = [
        "econ-paper-studio doctor",
        "=" * 60,
        f"Project root: {result['project_root']}",
        f"Python: {result['python_version']}",
        f"Checks: {result['passed']} passed, {result['failed']} failed",
        "",
    ]
    for item in result["checks"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"[{status}] {item['title']} - {item['detail']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local install and project health.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--root", default=None, help="Project root to check")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if any check fails")
    args = parser.parse_args()

    root = Path(args.root) if args.root else None
    result = run_checks(root)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))

    return 1 if args.strict and result["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
