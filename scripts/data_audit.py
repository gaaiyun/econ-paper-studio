#!/usr/bin/env python3
"""Empirical data validation gate for econ-paper-studio."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass
class DataAuditCheck:
    id: str
    title: str
    severity: str
    passed: bool
    evidence: str
    recommendation: str


@dataclass
class DataAuditResult:
    source: str
    rows: int
    columns: list[str]
    key_columns: list[str]
    score: float
    checks: list[DataAuditCheck]


def _severity_weight(severity: str) -> int:
    return {"critical": 3, "high": 2, "medium": 1}.get(severity, 1)


def _column_list(values: list[str] | None) -> list[str]:
    columns: list[str] = []
    for value in values or []:
        for item in value.split(","):
            col = item.strip()
            if col and col not in columns:
                columns.append(col)
    return columns


def _check(check_id: str, title: str, severity: str, passed: bool, evidence: str, recommendation: str) -> DataAuditCheck:
    return DataAuditCheck(
        id=check_id,
        title=title,
        severity=severity,
        passed=passed,
        evidence=evidence,
        recommendation=recommendation,
    )


def _missing_share(series: pd.Series) -> float:
    if len(series) == 0:
        return 1.0
    return float(series.isna().mean())


def _is_numeric_series(series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        return True
    non_missing = series.dropna()
    if non_missing.empty:
        return False
    converted = pd.to_numeric(non_missing, errors="coerce")
    return bool(converted.notna().all())


def _score_checks(checks: list[DataAuditCheck]) -> float:
    total = sum(_severity_weight(item.severity) for item in checks) or 1
    passed = sum(_severity_weight(item.severity) for item in checks if item.passed)
    return round(10 * passed / total, 1)


def audit_dataframe(
    df: pd.DataFrame,
    *,
    source: str,
    required_columns: list[str] | None = None,
    key_columns: list[str] | None = None,
    outcome: str | None = None,
    treatment: str | None = None,
    cluster: str | None = None,
    min_clusters: int = 30,
    max_missing_share: float = 0.2,
) -> DataAuditResult:
    """Audit a dataframe before econometric execution."""
    required = _column_list(required_columns)
    keys = _column_list(key_columns)
    checks: list[DataAuditCheck] = []

    checks.append(
        _check(
            "data.non_empty",
            "Dataset has observations",
            "critical",
            len(df) > 0,
            f"{len(df)} rows",
            "Load a non-empty analysis sample before estimating models.",
        )
    )

    for col in required:
        checks.append(
            _check(
                f"column.{col}",
                f"Required column present: {col}",
                "high",
                col in df.columns,
                "present" if col in df.columns else "missing",
                f"Add or rename `{col}` before running the empirical pipeline.",
            )
        )

    missing_key_columns = [col for col in keys if col not in df.columns]
    if keys:
        if missing_key_columns:
            checks.append(
                _check(
                    "key.unique",
                    "Analysis key is unique",
                    "critical",
                    False,
                    f"missing key columns: {', '.join(missing_key_columns)}",
                    "Fix the key columns before merges or panel estimators.",
                )
            )
        else:
            duplicate_rows = int(df.duplicated(keys, keep=False).sum())
            checks.append(
                _check(
                    "key.unique",
                    "Analysis key is unique",
                    "critical",
                    duplicate_rows == 0,
                    f"{duplicate_rows} duplicate key rows using {', '.join(keys)}",
                    "Resolve duplicate unit-time keys to avoid join explosion and double counting.",
                )
            )

    audit_missing_cols = _column_list([
        *(required or []),
        *([outcome] if outcome else []),
        *([treatment] if treatment else []),
        *([cluster] if cluster else []),
    ])
    for col in audit_missing_cols:
        if col not in df.columns:
            continue
        share = _missing_share(df[col])
        checks.append(
            _check(
                f"missing.{col}",
                f"Missing share acceptable: {col}",
                "medium",
                share <= max_missing_share,
                f"{share:.1%} missing",
                f"Inspect missingness in `{col}` and document sample restrictions.",
            )
        )

    if outcome:
        if outcome not in df.columns:
            checks.append(
                _check(
                    "outcome.numeric",
                    "Outcome is numeric",
                    "critical",
                    False,
                    f"{outcome} missing",
                    "Provide a numeric outcome column before estimation.",
                )
            )
        else:
            checks.append(
                _check(
                    "outcome.numeric",
                    "Outcome is numeric",
                    "critical",
                    _is_numeric_series(df[outcome]),
                    str(df[outcome].dtype),
                    "Convert the outcome to a numeric scale and handle nonnumeric codes explicitly.",
                )
            )

    if treatment:
        if treatment not in df.columns:
            checks.append(
                _check(
                    "treatment.variation",
                    "Treatment has variation",
                    "critical",
                    False,
                    f"{treatment} missing",
                    "Provide a treatment or policy timing variable with treated and untreated observations.",
                )
            )
        else:
            n_unique = int(df[treatment].dropna().nunique())
            checks.append(
                _check(
                    "treatment.variation",
                    "Treatment has variation",
                    "critical",
                    n_unique >= 2,
                    f"{n_unique} non-missing unique values",
                    "Check treatment coding; a constant treatment variable cannot identify an effect.",
                )
            )

    if cluster:
        if cluster not in df.columns:
            checks.append(
                _check(
                    "cluster.count",
                    "Cluster count supports clustered inference",
                    "high",
                    False,
                    f"{cluster} missing",
                    "Pass the treatment-assignment cluster column or revise the inference plan.",
                )
            )
        else:
            n_clusters = int(df[cluster].dropna().nunique())
            checks.append(
                _check(
                    "cluster.count",
                    "Cluster count supports clustered inference",
                    "high",
                    n_clusters >= min_clusters,
                    f"{n_clusters} clusters; minimum {min_clusters}",
                    "Use an inference method suitable for few clusters or expand the sample.",
                )
            )

    return DataAuditResult(
        source=source,
        rows=int(len(df)),
        columns=[str(col) for col in df.columns],
        key_columns=keys,
        score=_score_checks(checks),
        checks=checks,
    )


def audit_csv(
    path: Path,
    *,
    required_columns: list[str] | None = None,
    key_columns: list[str] | None = None,
    outcome: str | None = None,
    treatment: str | None = None,
    cluster: str | None = None,
    min_clusters: int = 30,
    max_missing_share: float = 0.2,
) -> DataAuditResult:
    df = pd.read_csv(path)
    return audit_dataframe(
        df,
        source=str(path),
        required_columns=required_columns,
        key_columns=key_columns,
        outcome=outcome,
        treatment=treatment,
        cluster=cluster,
        min_clusters=min_clusters,
        max_missing_share=max_missing_share,
    )


def render_report(result: DataAuditResult) -> str:
    passed = sum(1 for item in result.checks if item.passed)
    failed = len(result.checks) - passed
    lines = [
        "# Data Audit Report",
        "",
        f"- Source: `{result.source}`",
        f"- Rows: {result.rows}",
        f"- Columns: {len(result.columns)}",
        f"- Key columns: `{', '.join(result.key_columns) if result.key_columns else 'not specified'}`",
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
        lines.append("- No blocking data-audit issues found. Still verify data provenance and coding logs.")

    check_map = {item.id: item for item in result.checks}
    key_check = check_map.get("key.unique")
    cluster_check = check_map.get("cluster.count")
    missing_checks = [item for item in result.checks if item.id.startswith("missing.")]
    missing_summary = "; ".join(f"{item.title.split(': ', 1)[-1]} {item.evidence}" for item in missing_checks) or "not checked"
    join_risk = "low" if key_check and key_check.passed else "high or unknown"
    denominator = (
        "Analysis denominator is the audited CSV rows after the user-specified required/key/outcome/treatment filters. "
        "Any model-specific sample drop must be recorded in the evidence ledger."
    )
    lines.extend(
        [
            "",
            "## Data Contract",
            "",
            f"- Source: `{result.source}`",
            f"- Analysis grain: `{', '.join(result.key_columns) if result.key_columns else 'not specified'}`",
            f"- Join explosion risk: **{join_risk}** ({key_check.evidence if key_check else 'no key check requested'})",
            f"- Missingness boundary: {missing_summary}",
            f"- Denominator boundary: {denominator}",
            f"- Cluster level: {cluster_check.evidence if cluster_check else 'not specified'}",
            "- Claim boundary: this audit supports structural readiness only; causal claims still require executed models, diagnostics, and source-backed interpretation.",
        ]
    )

    lines.extend(
        [
            "",
            "## Scope Note",
            "",
            "This gate checks structural risks before estimation: duplicate keys, missingness, basic type issues, treatment variation, and cluster count. It does not certify that the data source is authoritative or that the final model is correctly specified.",
        ]
    )
    return "\n".join(lines)


def _print_text(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a CSV before econometric execution.")
    parser.add_argument("--csv", required=True, help="CSV file to audit")
    parser.add_argument("--required", action="append", default=[], help="Required column; can be repeated")
    parser.add_argument("--key", action="append", default=[], help="Key column; can be repeated")
    parser.add_argument("--outcome", help="Outcome column")
    parser.add_argument("--treatment", help="Treatment or policy variable")
    parser.add_argument("--cluster", help="Cluster column for inference")
    parser.add_argument("--min-clusters", type=int, default=30)
    parser.add_argument("--max-missing-share", type=float, default=0.2)
    parser.add_argument("--output", help="Write report to this path")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    parser.add_argument("--fail-on-critical", action="store_true", help="Return exit code 2 if any critical check fails")
    args = parser.parse_args()

    result = audit_csv(
        Path(args.csv),
        required_columns=args.required,
        key_columns=args.key,
        outcome=args.outcome,
        treatment=args.treatment,
        cluster=args.cluster,
        min_clusters=args.min_clusters,
        max_missing_share=args.max_missing_share,
    )
    text = json.dumps(asdict(result), ensure_ascii=False, indent=2) if args.json else render_report(result)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")

    _print_text(text)

    if args.fail_on_critical and any(item.severity == "critical" and not item.passed for item in result.checks):
        print("[error] Critical data-audit checks failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
