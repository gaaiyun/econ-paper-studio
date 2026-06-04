#!/usr/bin/env python3
"""Evidence ledger, claim audit, and reviewer gauntlet for empirical papers."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LedgerEntry:
    artifact_id: str
    title: str
    artifact_path: str
    code_path: str
    data_source: str
    sample: str
    model: str
    estimand: str
    cluster: str
    claims: list[str] = field(default_factory=list)
    status: str = "needs_verification"
    notes: str = ""


@dataclass
class EvidenceLedger:
    version: int = 1
    entries: list[LedgerEntry] = field(default_factory=list)


@dataclass
class LedgerAuditReport:
    score: float
    missing: list[str]
    entry_count: int


@dataclass
class ClaimAuditRow:
    claim: str
    supported: bool
    artifact_ids: list[str]
    citation_status: str
    causal_language: str
    recommendation: str


@dataclass
class ClaimAuditResult:
    paper_path: str
    ledger_path: str
    score: float
    rows: list[ClaimAuditRow]


@dataclass
class ReviewerResult:
    reviewer: str
    score: float
    finding: str
    recommendation: str


@dataclass
class ReviewerGauntletResult:
    paper_path: str
    ledger_path: str
    score: float
    reviews: list[ReviewerResult]


def _load_brief(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("brief must be a mapping")
    return raw


def _value(data: dict[str, Any], key: str, default: str = "[待填写]") -> str:
    value = data.get(key)
    if value is None or value == "":
        return default
    return str(value)


def render_design_memo(brief: dict[str, Any]) -> str:
    data = brief.get("data") if isinstance(brief.get("data"), dict) else {}
    unit = _value(data, "unit_id")
    time = _value(data, "time_id")
    outcome = _value(data, "outcome")
    treatment = _value(data, "treatment")
    strategy = _value(brief, "identification_seed", "unspecified")
    question = _value(brief, "question")
    contribution = _value(brief, "contribution")
    assumption = "Parallel trends" if strategy.lower() == "did" else "Design-specific identifying assumptions"
    return "\n".join(
        [
            "# Identification Design Memo",
            "",
            f"- Research question: {question}",
            f"- Contribution: {contribution}",
            f"- Primary design: {strategy}",
            f"- Unit: `{unit}`",
            f"- Time: `{time}`",
            f"- Treatment: `{treatment}`",
            f"- Outcome: `{outcome}`",
            "",
            "## Estimand",
            "",
            f"- Target estimand: effect of `{treatment}` on `{outcome}` for the analysis sample.",
            "- Unit of interpretation: keep it tied to the observed sample and policy setting.",
            "",
            "## Identification Contract",
            "",
            f"- Main assumption: {assumption}.",
            "- Required diagnostics: pre-trend/event-study for DiD, density for RDD, first stage for IV, overlap for matching/DML.",
            "- Threats to record: anticipation, selection, measurement error, spillovers, composition changes, and clustered inference risk.",
            "",
            "## Execution Boundary",
            "",
            "- 不得编造回归结果、样本量、引用或政策事实。",
            "- Every result table must be linked to code, data, sample, model, estimand, and cluster level in the evidence ledger.",
        ]
    )


def load_ledger(path: str | Path) -> EvidenceLedger:
    target = Path(path)
    raw = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"version": 1, "entries": []}
    entries = [LedgerEntry(**item) for item in raw.get("entries", [])]
    return EvidenceLedger(version=int(raw.get("version", 1)), entries=entries)


def write_ledger(path: str | Path, ledger: EvidenceLedger) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(ledger), ensure_ascii=False, indent=2), encoding="utf-8")


def audit_ledger(ledger: EvidenceLedger) -> LedgerAuditReport:
    required = ["artifact_path", "code_path", "data_source", "sample", "model", "estimand", "cluster"]
    missing: list[str] = []
    for entry in ledger.entries:
        for field_name in required:
            if not getattr(entry, field_name):
                missing.append(f"{entry.artifact_id}.{field_name}")
    total = max(1, len(ledger.entries) * len(required))
    score = round(10 * (total - len(missing)) / total, 1)
    return LedgerAuditReport(score=score, missing=missing, entry_count=len(ledger.entries))


def _read_text(path: str | Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_claims(text: str) -> list[str]:
    claims: list[str] = []
    for line in text.splitlines():
        for match in re.finditer(r"(?:^|\b)(?:claim|结论|主张)\s*[:：]\s*(.+)", line, flags=re.IGNORECASE):
            claims.append(match.group(1).strip())
    return claims


def _has_references(text: str) -> bool:
    return re.search(r"(?im)^\s*(?:#+\s*)?(references|bibliography|参考文献)\s*$", text) is not None


def _causal_language(claim: str) -> str:
    if re.search(r"\b(cause|causes|effect|reduce|increase|improve|impact)\b|因果|效应|影响", claim, re.I):
        return "causal-or-effect language"
    return "descriptive language"


def audit_claims(paper_path: str | Path, ledger_path: str | Path) -> ClaimAuditResult:
    text = _read_text(paper_path)
    ledger = load_ledger(ledger_path)
    claims = _extract_claims(text)
    rows: list[ClaimAuditRow] = []
    references = _has_references(text)
    for claim in claims:
        norm_claim = _normalize(claim)
        matched: list[str] = []
        for entry in ledger.entries:
            candidates = [entry.title, *entry.claims]
            if any(norm_claim and norm_claim in _normalize(candidate) for candidate in candidates):
                matched.append(entry.artifact_id)
        supported = bool(matched)
        rows.append(
            ClaimAuditRow(
                claim=claim,
                supported=supported,
                artifact_ids=matched,
                citation_status="references-section-present" if references else "references-section-missing",
                causal_language=_causal_language(claim),
                recommendation=(
                    "Keep artifact/code/data linkage current."
                    if supported
                    else "Link this claim to a ledger artifact or soften/remove it before submission."
                ),
            )
        )
    if not rows:
        rows.append(
            ClaimAuditRow(
                claim="[no explicit Claim: markers found]",
                supported=False,
                artifact_ids=[],
                citation_status="references-section-present" if references else "references-section-missing",
                causal_language="unknown",
                recommendation="Mark core empirical claims with `Claim:` so the agent can audit evidence links.",
            )
        )
    score = round(10 * sum(1 for row in rows if row.supported) / len(rows), 1)
    return ClaimAuditResult(str(paper_path), str(ledger_path), score, rows)


def run_reviewer_gauntlet(paper_path: str | Path, ledger_path: str | Path) -> ReviewerGauntletResult:
    text = _read_text(paper_path)
    ledger = load_ledger(ledger_path)
    claim_result = audit_claims(paper_path, ledger_path)
    ledger_report = audit_ledger(ledger)
    checks = [
        ReviewerResult(
            "Method Reviewer",
            8.0 if re.search(r"parallel trends|first stage|density|overlap|placebo", text, re.I) else 5.0,
            "Method diagnostics are mentioned." if re.search(r"parallel trends|first stage|density|overlap|placebo", text, re.I) else "Method diagnostics are thin.",
            "Tie every identifying assumption to a diagnostic and robustness table.",
        ),
        ReviewerResult(
            "Data Auditor",
            ledger_report.score,
            f"{ledger_report.entry_count} ledger entries; {len(ledger_report.missing)} missing fields.",
            "Resolve missing data/code/sample/model fields in the ledger.",
        ),
        ReviewerResult(
            "Citation Auditor",
            8.0 if _has_references(text) else 4.0,
            "References section found." if _has_references(text) else "References section missing.",
            "Verify each cited source with DOI, journal page, OpenAlex, Crossref, or manual lookup.",
        ),
        ReviewerResult(
            "Writing/Humanizer",
            8.0 if not re.search(r"valuable insights|important role|值得注意的是|具有重要", text, re.I) else 5.0,
            "No common filler phrase found." if not re.search(r"valuable insights|important role|值得注意的是|具有重要", text, re.I) else "Generic filler phrase found.",
            "Replace generic emphasis with concrete estimates, design facts, and limitations.",
        ),
        ReviewerResult(
            "Replication Editor",
            8.0 if claim_result.score >= 7 and ledger.entries else 5.0,
            f"Claim audit score {claim_result.score:.1f}; ledger entries {len(ledger.entries)}.",
            "Make sure every table and figure can be recreated from recorded code paths.",
        ),
    ]
    score = round(sum(item.score for item in checks) / len(checks), 1)
    return ReviewerGauntletResult(str(paper_path), str(ledger_path), score, checks)


def render_ledger_audit(report: LedgerAuditReport) -> str:
    lines = [
        "# Evidence Ledger Audit",
        "",
        f"- Score: **{report.score:.1f} / 10**",
        f"- Entries: {report.entry_count}",
        "",
        "## Missing Fields",
        "",
    ]
    lines.extend([f"- {item}" for item in report.missing] or ["- No missing required ledger fields found."])
    return "\n".join(lines)


def render_claim_audit(result: ClaimAuditResult) -> str:
    lines = [
        "# Claim-to-Evidence Audit",
        "",
        f"- Paper: `{result.paper_path}`",
        f"- Ledger: `{result.ledger_path}`",
        f"- Score: **{result.score:.1f} / 10**",
        "",
        "| Supported | Claim | Artifacts | Citation status | Language |",
        "|---|---|---|---|---|",
    ]
    for row in result.rows:
        lines.append(
            f"| {'yes' if row.supported else 'no'} | {row.claim} | {', '.join(row.artifact_ids) or '-'} | {row.citation_status} | {row.causal_language} |"
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {row.recommendation}" for row in result.rows if not row.supported)
    if all(row.supported for row in result.rows):
        lines.append("- Keep citation verification and numerical reproduction logs with the final package.")
    return "\n".join(lines)


def render_reviewer_gauntlet(result: ReviewerGauntletResult) -> str:
    lines = [
        "# Reviewer Gauntlet",
        "",
        f"- Score: **{result.score:.1f} / 10**",
        "",
        "| Reviewer | Score | Finding | Recommendation |",
        "|---|---:|---|---|",
    ]
    for review in result.reviews:
        lines.append(f"| {review.reviewer} | {review.score:.1f} | {review.finding} | {review.recommendation} |")
    return "\n".join(lines)


def _print_text(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evidence memo, ledger, claim audit, and reviewer gauntlet.")
    sub = parser.add_subparsers(dest="command", required=True)

    memo_parser = sub.add_parser("design-memo", help="Render an identification design memo from a brief")
    memo_parser.add_argument("--brief", required=True)
    memo_parser.add_argument("--output")

    ledger_parser = sub.add_parser("ledger", help="Manage the evidence ledger")
    ledger_sub = ledger_parser.add_subparsers(dest="ledger_command", required=True)
    ledger_init = ledger_sub.add_parser("init", help="Create an empty ledger")
    ledger_init.add_argument("--ledger", required=True)
    ledger_add = ledger_sub.add_parser("add", help="Add one ledger entry")
    ledger_add.add_argument("--ledger", required=True)
    for arg in ["artifact-id", "title", "artifact-path", "code-path", "data-source", "sample", "model", "estimand", "cluster"]:
        ledger_add.add_argument(f"--{arg}", required=True)
    ledger_add.add_argument("--claim", action="append", default=[])
    ledger_add.add_argument("--status", default="needs_verification")
    ledger_add.add_argument("--notes", default="")
    ledger_audit = ledger_sub.add_parser("audit", help="Audit ledger completeness")
    ledger_audit.add_argument("--ledger", required=True)
    ledger_audit.add_argument("--json", action="store_true")

    claim_parser = sub.add_parser("claim-audit", help="Audit paper claims against a ledger")
    claim_parser.add_argument("--paper", required=True)
    claim_parser.add_argument("--ledger", required=True)
    claim_parser.add_argument("--json", action="store_true")
    claim_parser.add_argument("--output")

    reviewer_parser = sub.add_parser("reviewer-gauntlet", help="Run reviewer checks")
    reviewer_parser.add_argument("--paper", required=True)
    reviewer_parser.add_argument("--ledger", required=True)
    reviewer_parser.add_argument("--json", action="store_true")
    reviewer_parser.add_argument("--output")

    args = parser.parse_args()
    if args.command == "design-memo":
        text = render_design_memo(_load_brief(Path(args.brief)))
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(text, encoding="utf-8")
        _print_text(text)
        return 0
    if args.command == "ledger":
        if args.ledger_command == "init":
            write_ledger(args.ledger, EvidenceLedger())
            _print_text(f"initialized ledger: {args.ledger}")
            return 0
        if args.ledger_command == "add":
            ledger = load_ledger(args.ledger)
            ledger.entries.append(
                LedgerEntry(
                    artifact_id=args.artifact_id,
                    title=args.title,
                    artifact_path=args.artifact_path,
                    code_path=args.code_path,
                    data_source=args.data_source,
                    sample=args.sample,
                    model=args.model,
                    estimand=args.estimand,
                    cluster=args.cluster,
                    claims=args.claim,
                    status=args.status,
                    notes=args.notes,
                )
            )
            write_ledger(args.ledger, ledger)
            _print_text(f"added ledger entry: {args.artifact_id}")
            return 0
        if args.ledger_command == "audit":
            report = audit_ledger(load_ledger(args.ledger))
            text = json.dumps(asdict(report), ensure_ascii=False, indent=2) if args.json else render_ledger_audit(report)
            _print_text(text)
            return 0
    if args.command == "claim-audit":
        result = audit_claims(args.paper, args.ledger)
        text = json.dumps(asdict(result), ensure_ascii=False, indent=2) if args.json else render_claim_audit(result)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(text, encoding="utf-8")
        _print_text(text)
        return 0
    if args.command == "reviewer-gauntlet":
        result = run_reviewer_gauntlet(args.paper, args.ledger)
        text = json.dumps(asdict(result), ensure_ascii=False, indent=2) if args.json else render_reviewer_gauntlet(result)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(text, encoding="utf-8")
        _print_text(text)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
