"""doctor.py tests -- local project health checks."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from doctor import run_checks

DOCTOR_PY = Path(__file__).resolve().parent.parent / "scripts" / "doctor.py"


def test_run_checks_reports_required_project_files():
    result = run_checks(Path(__file__).resolve().parent.parent)
    checks = {item["id"]: item for item in result["checks"]}

    assert result["project_root"].endswith("econ-paper-studio")
    assert checks["file.README.md"]["passed"]
    assert checks["file.scripts/cli.py"]["passed"]
    assert checks["file.scripts/robustness_checks.py"]["passed"]


def test_doctor_cli_json_output_is_parseable():
    proc = subprocess.run(
        [sys.executable, str(DOCTOR_PY), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert "checks" in data
    assert "python_version" in data
