"""robustness_checks.py tests -- static Stage 4 verification."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from robustness_checks import (
    evaluate_analysis,
    render_report,
    scan_anti_ai_phrases,
    scan_causal_overclaims,
    scan_citation_risks,
)
from scaffold import STATA_TEMPLATES, write_files

VERIFY_PY = Path(__file__).resolve().parent.parent / "scripts" / "robustness_checks.py"


def test_did_static_checks_pass_on_generated_stata_scaffold(tmp_path):
    analysis_dir = tmp_path / "paper"
    write_files(analysis_dir / "do", STATA_TEMPLATES["DiD"],
                session="paper", ts="2026-06-02")

    result = evaluate_analysis(strategy="DiD", analysis_dir=analysis_dir)

    checks = {item.id: item for item in result.checks}
    assert checks["did.cluster_se"].passed
    assert checks["did.parallel_trends"].passed
    assert checks["did.placebo"].passed
    assert checks["did.modern_staggered"].passed
    assert checks["did.multiple_testing"].passed
    assert result.score == 10


def test_anti_ai_scan_flags_common_machine_phrases(tmp_path):
    paper = tmp_path / "draft.md"
    paper.write_text(
        "It is worth noting that this paper provides valuable insights.\n",
        encoding="utf-8",
    )

    checks = scan_anti_ai_phrases([paper])

    assert checks
    assert not checks[0].passed
    assert "It is worth noting" in checks[0].evidence


def test_citation_scan_flags_placeholders_and_missing_references(tmp_path):
    paper = tmp_path / "draft.md"
    paper.write_text(
        "Following Author (YYYY), we estimate the model. [citation needed]\n",
        encoding="utf-8",
    )

    checks = scan_citation_risks([paper])
    by_id = {item.id: item for item in checks}

    assert not by_id["citation.placeholders"].passed
    assert not by_id["citation.references_section"].passed


def test_causal_overclaim_scan_flags_strong_claim_without_qualification(tmp_path):
    paper = tmp_path / "draft.md"
    paper.write_text(
        "Our estimates robustly demonstrate a causal effect of minimum wage on employment.\n",
        encoding="utf-8",
    )

    checks = scan_causal_overclaims([paper])

    assert checks
    assert not checks[0].passed
    assert "robustly demonstrate" in checks[0].evidence.lower()


def test_render_report_includes_failed_next_actions(tmp_path):
    result = evaluate_analysis(strategy="DiD", analysis_dir=tmp_path)

    report = render_report(result)

    assert "# Verification Report" in report
    assert "Next Actions" in report
    assert "[FAIL]" in report


def test_cli_writes_markdown_report(tmp_path):
    analysis_dir = tmp_path / "analysis"
    write_files(analysis_dir / "do", STATA_TEMPLATES["DiD"],
                session="paper", ts="2026-06-02")
    out_file = tmp_path / "verify_report.md"

    proc = subprocess.run(
        [
            sys.executable, str(VERIFY_PY),
            "--strategy", "DiD",
            "--analysis", str(analysis_dir),
            "--output", str(out_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 0, proc.stderr
    assert out_file.exists()
    assert "Verification Report" in out_file.read_text(encoding="utf-8")


def test_cli_fail_under_returns_2_for_low_score(tmp_path):
    proc = subprocess.run(
        [
            sys.executable, str(VERIFY_PY),
            "--strategy", "DiD",
            "--analysis", str(tmp_path),
            "--fail-under", "9",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 2
    assert "below threshold" in proc.stderr.lower()
