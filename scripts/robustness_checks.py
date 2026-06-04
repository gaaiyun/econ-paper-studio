#!/usr/bin/env python3
"""
robustness_checks.py - stage 4 static verification.

The verifier is intentionally offline-first. It does not claim to prove that an
estimate is correct or that a citation supports a claim. It checks whether the
analysis package and paper draft contain the minimum evidence hooks a reviewer
will expect: method-specific robustness code, cluster/weak-IV/bandwidth checks,
anti-AI prose flags, and obvious citation placeholders.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

TEXT_SUFFIXES = {".do", ".r", ".py", ".md", ".txt", ".tex"}


@dataclass
class CheckResult:
    id: str
    title: str
    severity: str
    passed: bool
    evidence: str
    recommendation: str


@dataclass
class VerificationResult:
    strategy: str
    analysis_dir: str
    paper_files: list[str]
    score: float
    checks: list[CheckResult]


def _severity_weight(severity: str) -> int:
    return {"critical": 3, "high": 2, "medium": 1}.get(severity, 1)


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def collect_text(paths: list[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            chunks.append(_read_text_file(path))
        elif path.is_dir():
            for sub in path.rglob("*"):
                if sub.is_file() and sub.suffix.lower() in TEXT_SUFFIXES:
                    chunks.append(_read_text_file(sub))
    return "\n".join(chunks)


def _match_any(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(0)[:120]
    return None


def _check_pattern(
    text: str,
    *,
    check_id: str,
    title: str,
    severity: str,
    patterns: list[str],
    recommendation: str,
) -> CheckResult:
    evidence = _match_any(text, patterns)
    return CheckResult(
        id=check_id,
        title=title,
        severity=severity,
        passed=evidence is not None,
        evidence=evidence or "No matching evidence found.",
        recommendation=recommendation,
    )


METHOD_CHECKS: dict[str, list[dict[str, object]]] = {
    "DiD": [
        {
            "id": "did.cluster_se",
            "title": "Clustered standard errors",
            "severity": "critical",
            "patterns": [r"\bcluster\s*\(", r"\bcluster\s*=", r"vce\s*\(\s*cluster"],
            "recommendation": "Cluster at the treatment assignment level, not merely the observation level.",
        },
        {
            "id": "did.parallel_trends",
            "title": "Parallel trends / event-study evidence",
            "severity": "critical",
            "patterns": [r"event[\s_-]?study", r"parallel trends?", r"\blead[_-]?lag\b", r"\biplot\s*\("],
            "recommendation": "Add an event-study or pre-trend diagnostic before interpreting DiD as causal.",
        },
        {
            "id": "did.modern_staggered",
            "title": "Modern staggered DiD alternative",
            "severity": "high",
            "patterns": [r"\bcsdid\b", r"callaway", r"sant'?anna", r"sun[\s_-]?abraham", r"\batt_gt\b", r"honestdid"],
            "recommendation": "For staggered adoption, include CS-DiD, Sun-Abraham, BJS, or HonestDiD sensitivity.",
        },
        {
            "id": "did.placebo",
            "title": "Placebo timing or placebo group",
            "severity": "high",
            "patterns": [r"placebo", r"false treatment", r"虚假", r"安慰剂"],
            "recommendation": "Run false timing or false group placebo checks.",
        },
        {
            "id": "did.multiple_testing",
            "title": "Multiple testing correction",
            "severity": "medium",
            "patterns": [r"bonferroni", r"holm", r"romano", r"rwolf", r"multiple testing", r"多重"],
            "recommendation": "If there are multiple outcomes or subgroups, add Bonferroni/Holm/Romano-Wolf correction.",
        },
    ],
    "RDD": [
        {
            "id": "rdd.main",
            "title": "RD main estimator",
            "severity": "critical",
            "patterns": [r"\brdrobust\b", r"\brdd\b", r"regression discontinuity"],
            "recommendation": "Use a recognized RD estimator such as rdrobust with explicit cutoff.",
        },
        {
            "id": "rdd.manipulation",
            "title": "Running-variable manipulation check",
            "severity": "critical",
            "patterns": [r"\brddensity\b", r"mccrary", r"density"],
            "recommendation": "Add McCrary/Cattaneo-Jansson-Ma density testing near the cutoff.",
        },
        {
            "id": "rdd.bandwidth",
            "title": "Bandwidth sensitivity",
            "severity": "high",
            "patterns": [r"bwselect", r"bandwidth", r"\bh\s*\("],
            "recommendation": "Report sensitivity to alternative bandwidth choices.",
        },
        {
            "id": "rdd.placebo_cutoff",
            "title": "Placebo cutoff",
            "severity": "high",
            "patterns": [r"placebo", r"false cutoff", r"c\s*\(\s*-", r"c\s*\(\s*0\.[1-9]", r"安慰剂"],
            "recommendation": "Run placebo cutoffs away from the real threshold.",
        },
        {
            "id": "rdd.donut",
            "title": "Donut RD",
            "severity": "medium",
            "patterns": [r"donut", r"abs\s*\([^)]*\)\s*>", r"剔除.*cutoff"],
            "recommendation": "Consider excluding observations very close to the cutoff.",
        },
    ],
    "IV": [
        {
            "id": "iv.first_stage",
            "title": "First-stage / weak-IV diagnostic",
            "severity": "critical",
            "patterns": [r"first[\s-]?stage", r"weak instrument", r"\bf\s*>\s*10", r"estat firststage"],
            "recommendation": "Report first-stage strength and weak-IV robust inference.",
        },
        {
            "id": "iv.exclusion",
            "title": "Exclusion restriction discussion",
            "severity": "critical",
            "patterns": [r"exclusion restriction", r"排除限制"],
            "recommendation": "State why the instrument affects the outcome only through treatment.",
        },
        {
            "id": "iv.overid",
            "title": "Over-identification test",
            "severity": "medium",
            "patterns": [r"over[\s-]?id", r"sargan", r"hansen"],
            "recommendation": "If multiple instruments are used, report over-identification diagnostics.",
        },
        {
            "id": "iv.weak_robust_ci",
            "title": "Weak-IV robust confidence interval",
            "severity": "high",
            "patterns": [r"anderson[\s-]?rubin", r"\bliml\b", r"weak[\s-]?robust"],
            "recommendation": "Add Anderson-Rubin or LIML sensitivity when weak-IV risk exists.",
        },
    ],
    "SCM": [
        {
            "id": "scm.estimator",
            "title": "Synthetic control estimator",
            "severity": "critical",
            "patterns": [r"\bsynth\b", r"synthetic control", r"\bscm\b"],
            "recommendation": "Use a recognized SCM/ASCM/SDID estimator.",
        },
        {
            "id": "scm.pre_fit",
            "title": "Pre-period fit / RMSPE",
            "severity": "critical",
            "patterns": [r"rmspe", r"pre[\s-]?period", r"pre[\s-]?fit"],
            "recommendation": "Report pre-treatment fit quality before interpreting post-treatment gaps.",
        },
        {
            "id": "scm.placebo",
            "title": "In-space or in-time placebo",
            "severity": "high",
            "patterns": [r"placebo", r"in[\s-]?space", r"in[\s-]?time"],
            "recommendation": "Run placebo tests across donor units or false treatment dates.",
        },
        {
            "id": "scm.leave_one_out",
            "title": "Leave-one-out donor sensitivity",
            "severity": "medium",
            "patterns": [r"leave[\s-]?one[\s-]?out", r"donor"],
            "recommendation": "Check whether one donor drives the synthetic control.",
        },
    ],
    "PSM": [
        {
            "id": "psm.balance",
            "title": "Covariate balance",
            "severity": "critical",
            "patterns": [r"balance", r"standardized difference", r"std\.? diff", r"协变量平衡"],
            "recommendation": "Report post-match covariate balance, not only treatment effects.",
        },
        {
            "id": "psm.common_support",
            "title": "Common support",
            "severity": "critical",
            "patterns": [r"common support", r"overlap", r"共同支撑"],
            "recommendation": "Show overlap/common support before matching estimates.",
        },
        {
            "id": "psm.sensitivity",
            "title": "Selection-on-observables sensitivity",
            "severity": "high",
            "patterns": [r"rosenbaum", r"sensitivity", r"entropy balancing"],
            "recommendation": "Add Rosenbaum bounds or a stronger balancing alternative such as entropy balancing.",
        },
    ],
    "DML": [
        {
            "id": "dml.cross_fit",
            "title": "Cross-fitting",
            "severity": "critical",
            "patterns": [r"cross[\s-]?fit", r"k[\s-]?fold", r"sample[\s-]?split"],
            "recommendation": "Use cross-fitting to avoid overfitting nuisance models.",
        },
        {
            "id": "dml.multiple_learners",
            "title": "Alternative nuisance learners",
            "severity": "high",
            "patterns": [r"lasso", r"random forest", r"xgboost", r"neural", r"learner"],
            "recommendation": "Compare at least two nuisance learner families.",
        },
        {
            "id": "dml.hyperparams",
            "title": "Hyperparameter sensitivity",
            "severity": "medium",
            "patterns": [r"hyperparameter", r"grid", r"tuning"],
            "recommendation": "Record tuning choices and sensitivity to key hyperparameters.",
        },
    ],
}


ANTI_AI_PATTERNS = [
    (r"\bIt is worth noting that\b", "It is worth noting"),
    (r"\bIt is important to note that\b", "It is important to note"),
    (r"\bprovides? valuable insights?\b", "provides valuable insights"),
    (r"\bplays? an? (crucial|important|significant) role\b", "plays a crucial role"),
    (r"\bcomprehensive analysis\b", "comprehensive analysis"),
    (r"\bin-depth (examination|analysis)\b", "in-depth analysis"),
    (r"值得注意的是", "值得注意的是"),
    (r"具有重要的现实意义", "具有重要的现实意义"),
    (r"进一步丰富了.*研究", "进一步丰富了...研究"),
]


def scan_anti_ai_phrases(paper_files: list[Path]) -> list[CheckResult]:
    text = collect_text(paper_files)
    if not paper_files:
        return []
    hits: list[str] = []
    for pattern, label in ANTI_AI_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            hits.append(label)
    return [
        CheckResult(
            id="writing.anti_ai_phrases",
            title="AI-like filler phrases",
            severity="medium",
            passed=not hits,
            evidence=", ".join(hits[:8]) if hits else "No common AI-style filler phrases found.",
            recommendation="Replace filler with concrete claims, numbers, or direct transitions.",
        )
    ]


def scan_citation_risks(paper_files: list[Path]) -> list[CheckResult]:
    text = collect_text(paper_files)
    if not paper_files:
        return []

    placeholder_patterns = [
        r"Author\s*\(\s*YYYY\s*\)",
        r"\([A-Za-z ]+,\s*YYYY\)",
        r"\[citation needed\]",
        r"\bTODO\b.*cit",
        r"\?\?",
    ]
    placeholder = _match_any(text, placeholder_patterns)
    has_references = re.search(r"(?im)^\s*(?:#+\s*)?(references|bibliography|参考文献)\s*$", text) is not None
    has_author_year = (
        re.search(r"\([A-Z][A-Za-z'&.\-\s]+,\s*(?:19|20)\d{2}[a-z]?\)", text) is not None
        or placeholder is not None
    )
    if has_references:
        references_evidence = "References section found."
    elif has_author_year:
        references_evidence = "Author-year citations found but no references section."
    else:
        references_evidence = "No author-year citations detected in scanned draft."

    checks = [
        CheckResult(
            id="citation.placeholders",
            title="Citation placeholders",
            severity="high",
            passed=placeholder is None,
            evidence=placeholder or "No obvious citation placeholders found.",
            recommendation="Replace every placeholder with a verified source before submission.",
        ),
        CheckResult(
            id="citation.references_section",
            title="References section present",
            severity="medium",
            passed=has_references or not has_author_year,
            evidence=references_evidence,
            recommendation="Keep a complete references section or BibTeX file with the draft.",
        ),
    ]
    return checks


CAUSAL_OVERCLAIM_PATTERNS = [
    r"\brobustly demonstrates?\b",
    r"\bconclusively (shows?|demonstrates?|proves?)\b",
    r"\bproves? a causal\b",
    r"\bcausal effect\b",
    r"\bcauses?\b",
    r"强有力地证明",
    r"充分证明",
    r"因果效应",
]

QUALIFICATION_PATTERNS = [
    r"\bidentification\b",
    r"\bparallel trends?\b",
    r"\brobustness\b",
    r"\blimitation\b",
    r"\bsensitivity\b",
    r"识别",
    r"稳健性",
    r"平行趋势",
    r"敏感性",
    r"局限",
]


def scan_causal_overclaims(paper_files: list[Path]) -> list[CheckResult]:
    text = collect_text(paper_files)
    if not paper_files:
        return []

    claim = _match_any(text, CAUSAL_OVERCLAIM_PATTERNS)
    qualification = _match_any(text, QUALIFICATION_PATTERNS)
    passed = claim is None or qualification is not None
    evidence = (
        "No strong causal overclaim phrases found."
        if claim is None
        else f"Claim: {claim}; qualification: {qualification or 'none found'}"
    )
    return [
        CheckResult(
            id="writing.causal_overclaim",
            title="Causal overclaim risk",
            severity="high",
            passed=passed,
            evidence=evidence,
            recommendation=(
                "Qualify strong causal claims with the identification assumption, robustness evidence, "
                "or sensitivity limits before submission."
            ),
        )
    ]


def evaluate_analysis(
    *,
    strategy: str,
    analysis_dir: Path,
    paper_files: list[Path] | None = None,
) -> VerificationResult:
    normalized = "PSM" if strategy.lower() in {"matching", "match"} else strategy
    text = collect_text([analysis_dir])
    checks: list[CheckResult] = []

    for item in METHOD_CHECKS.get(normalized, []):
        checks.append(
            _check_pattern(
                text,
                check_id=str(item["id"]),
                title=str(item["title"]),
                severity=str(item["severity"]),
                patterns=list(item["patterns"]),
                recommendation=str(item["recommendation"]),
            )
        )

    papers = paper_files or []
    checks.extend(scan_anti_ai_phrases(papers))
    checks.extend(scan_citation_risks(papers))
    checks.extend(scan_causal_overclaims(papers))

    total_weight = sum(_severity_weight(c.severity) for c in checks) or 1
    passed_weight = sum(_severity_weight(c.severity) for c in checks if c.passed)
    score = round(10 * passed_weight / total_weight, 1)

    return VerificationResult(
        strategy=normalized,
        analysis_dir=str(analysis_dir),
        paper_files=[str(p) for p in papers],
        score=score,
        checks=checks,
    )


def render_report(result: VerificationResult) -> str:
    passed = sum(1 for c in result.checks if c.passed)
    failed = len(result.checks) - passed
    lines = [
        "# Verification Report",
        "",
        f"- Strategy: `{result.strategy}`",
        f"- Analysis path: `{result.analysis_dir}`",
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

    failed_checks = [c for c in result.checks if not c.passed]
    lines.extend(["", "## Next Actions", ""])
    if failed_checks:
        for check in failed_checks:
            lines.append(f"- [{check.severity}] {check.recommendation}")
    else:
        lines.append("- No blocking static issues found. Still verify numerical outputs and sources manually.")

    lines.extend([
        "",
        "## Scope Note",
        "",
        "This is an offline static verifier. It checks for evidence hooks in code and prose; it does not validate numerical correctness or prove that cited papers support the claims.",
    ])
    return "\n".join(lines)


def _print_text(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline robustness, writing, and citation checks.")
    parser.add_argument("--strategy", required=True, choices=["DiD", "RDD", "IV", "SCM", "PSM", "Matching", "DML"])
    parser.add_argument("--analysis", required=True, help="Analysis/session directory to scan")
    parser.add_argument("--paper", action="append", default=[], help="Optional paper draft (.md/.tex/.txt)")
    parser.add_argument("--output", help="Write Markdown report to this path")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    parser.add_argument("--fail-under", type=float, default=None,
                        help="Return exit code 2 if score is below this threshold")
    args = parser.parse_args()

    analysis_dir = Path(args.analysis)
    paper_files = [Path(p) for p in args.paper]
    result = evaluate_analysis(strategy=args.strategy, analysis_dir=analysis_dir, paper_files=paper_files)

    text = json.dumps(asdict(result), ensure_ascii=False, indent=2) if args.json else render_report(result)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")

    _print_text(text)

    if args.fail_under is not None and result.score < args.fail_under:
        print(f"[error] Verification score {result.score:.1f} below threshold {args.fail_under:.1f}",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
