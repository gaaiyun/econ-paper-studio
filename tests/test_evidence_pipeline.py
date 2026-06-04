"""evidence_pipeline.py tests -- memo, ledger, claim audit, and reviewer gauntlet."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from evidence_pipeline import (
    audit_claims,
    audit_ledger,
    load_ledger,
    render_design_memo,
    run_reviewer_gauntlet,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PY = PROJECT_ROOT / "scripts" / "evidence_pipeline.py"


def _brief() -> dict[str, object]:
    return {
        "question": "最低工资调整对青年就业率有什么影响？",
        "contribution": "使用城市-年份面板识别错时政策调整。",
        "identification_seed": "DiD",
        "data": {
            "unit_id": "city_id",
            "time_id": "year",
            "outcome": "youth_employment_rate",
            "treatment": "minimum_wage_increase",
        },
    }


def test_render_design_memo_contains_identification_contract():
    memo = render_design_memo(_brief())

    assert "# Identification Design Memo" in memo
    assert "Estimand" in memo
    assert "Parallel trends" in memo
    assert "city_id" in memo
    assert "不得编造" in memo


def test_ledger_init_add_audit_cli_roundtrip(tmp_path):
    ledger_path = tmp_path / "ledger.json"

    init_proc = subprocess.run(
        [sys.executable, str(EVIDENCE_PY), "ledger", "init", "--ledger", str(ledger_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    add_proc = subprocess.run(
        [
            sys.executable,
            str(EVIDENCE_PY),
            "ledger",
            "add",
            "--ledger",
            str(ledger_path),
            "--artifact-id",
            "table1",
            "--title",
            "Baseline DiD estimates",
            "--artifact-path",
            "tables/table1.tex",
            "--code-path",
            "do/03_main.do",
            "--data-source",
            "analysis_panel_v1.csv",
            "--sample",
            "city-year panel",
            "--model",
            "two-way fixed effects DiD",
            "--estimand",
            "ATT",
            "--cluster",
            "city_id",
            "--claim",
            "Minimum wage increases reduce youth employment",
            "--status",
            "needs_verification",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert init_proc.returncode == 0
    assert add_proc.returncode == 0
    ledger = load_ledger(ledger_path)
    assert ledger.entries[0].artifact_id == "table1"
    report = audit_ledger(ledger)
    assert report.score >= 8


def test_claim_audit_links_claims_to_ledger_and_flags_unsupported(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text(
        "# Draft\n\n"
        "## Results\n\n"
        "Claim: Minimum wage increases reduce youth employment.\n\n"
        "Claim: The mechanism is stronger for export firms.\n\n"
        "## References\n\n"
        "Card, D. and Krueger, A. 1994. Minimum Wages and Employment.\n",
        encoding="utf-8",
    )
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "artifact_id": "table1",
                        "title": "Minimum wage increases reduce youth employment",
                        "artifact_path": "tables/table1.tex",
                        "code_path": "do/03_main.do",
                        "data_source": "analysis_panel_v1.csv",
                        "sample": "city-year panel",
                        "model": "DiD",
                        "estimand": "ATT",
                        "cluster": "city_id",
                        "claims": ["Minimum wage increases reduce youth employment"],
                        "status": "verified",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = audit_claims(draft, ledger_path)

    rows = {row.claim: row for row in result.rows}
    assert rows["Minimum wage increases reduce youth employment."].supported
    assert not rows["The mechanism is stronger for export firms."].supported
    assert result.score < 10


def test_reviewer_gauntlet_reports_method_data_writing_and_replication(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text(
        "## Introduction\n\n"
        "Claim: Minimum wage increases reduce youth employment.\n\n"
        "## Data\n\n"
        "The sample is a city-year panel.\n\n"
        "## Empirical Strategy\n\n"
        "We use DiD and discuss parallel trends.\n\n"
        "## Results\n\n"
        "Table 1. Baseline estimates for the city-year panel clustered by city.\n\n"
        "## Robustness\n\n"
        "We report placebo tests.\n\n"
        "## References\n\n"
        "Card, D. and Krueger, A. 1994.\n",
        encoding="utf-8",
    )
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "artifact_id": "table1",
                        "title": "Baseline estimates",
                        "artifact_path": "tables/table1.tex",
                        "code_path": "do/03_main.do",
                        "data_source": "analysis_panel_v1.csv",
                        "sample": "city-year panel",
                        "model": "DiD",
                        "estimand": "ATT",
                        "cluster": "city_id",
                        "claims": ["Minimum wage increases reduce youth employment"],
                        "status": "verified",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = run_reviewer_gauntlet(draft, ledger_path)
    names = {item.reviewer for item in result.reviews}

    assert {"Method Reviewer", "Data Auditor", "Citation Auditor", "Writing/Humanizer", "Replication Editor"} <= names
    assert result.score >= 7
