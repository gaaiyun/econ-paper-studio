"""data_audit.py tests -- empirical data validation gate."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from data_audit import audit_dataframe, render_report

DATA_AUDIT_PY = Path(__file__).resolve().parent.parent / "scripts" / "data_audit.py"


def test_audit_dataframe_flags_duplicate_panel_keys_and_low_cluster_count():
    df = pd.DataFrame(
        {
            "city_id": [1, 1, 1, 2],
            "year": [2020, 2020, 2021, 2020],
            "treated": [0, 1, 1, 1],
            "employment": [0.52, 0.53, 0.55, 0.50],
        }
    )

    result = audit_dataframe(
        df,
        source="inline",
        required_columns=["city_id", "year", "treated", "employment"],
        key_columns=["city_id", "year"],
        outcome="employment",
        treatment="treated",
        cluster="city_id",
        min_clusters=3,
    )
    checks = {item.id: item for item in result.checks}

    assert not checks["key.unique"].passed
    assert "2 duplicate" in checks["key.unique"].evidence
    assert not checks["cluster.count"].passed
    assert result.score < 10


def test_audit_dataframe_passes_clean_minimum_panel():
    df = pd.DataFrame(
        {
            "city_id": [1, 1, 2, 2, 3, 3],
            "year": [2020, 2021, 2020, 2021, 2020, 2021],
            "treated": [0, 1, 0, 1, 0, 1],
            "employment": [0.52, 0.53, 0.55, 0.56, 0.51, 0.54],
        }
    )

    result = audit_dataframe(
        df,
        source="inline",
        required_columns=["city_id", "year", "treated", "employment"],
        key_columns=["city_id", "year"],
        outcome="employment",
        treatment="treated",
        cluster="city_id",
        min_clusters=3,
    )

    assert result.score == 10
    assert all(item.passed for item in result.checks)


def test_render_report_includes_next_actions_for_failed_checks():
    df = pd.DataFrame({"unit": [1, 1], "y": ["bad", "data"]})
    result = audit_dataframe(df, source="inline", key_columns=["unit"], outcome="y")

    report = render_report(result)

    assert "# Data Audit Report" in report
    assert "Next Actions" in report
    assert "[FAIL]" in report


def test_render_report_includes_data_contract_for_agent_execution():
    df = pd.DataFrame(
        {
            "city_id": [1, 1, 2, 2],
            "year": [2020, 2021, 2020, 2021],
            "treated": [0, 1, 0, 1],
            "employment": [0.52, 0.53, 0.55, 0.56],
        }
    )
    result = audit_dataframe(
        df,
        source="inline",
        key_columns=["city_id", "year"],
        outcome="employment",
        treatment="treated",
        cluster="city_id",
        min_clusters=2,
    )

    report = render_report(result)

    assert "## Data Contract" in report
    assert "Join explosion risk" in report
    assert "Denominator boundary" in report
    assert "Cluster level" in report


def test_data_audit_cli_outputs_json_and_fail_on_critical(tmp_path):
    csv_path = tmp_path / "panel.csv"
    csv_path.write_text(
        "city_id,year,treated,employment\n"
        "1,2020,0,0.52\n"
        "1,2020,1,0.53\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(DATA_AUDIT_PY),
            "--csv",
            str(csv_path),
            "--key",
            "city_id",
            "--key",
            "year",
            "--outcome",
            "employment",
            "--treatment",
            "treated",
            "--json",
            "--fail-on-critical",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 2
    data = json.loads(proc.stdout)
    assert data["rows"] == 2
    assert any(item["id"] == "key.unique" and not item["passed"] for item in data["checks"])
