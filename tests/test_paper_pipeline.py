"""paper_pipeline.py tests -- writing, citation, and reviewer-readiness gate."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from paper_pipeline import audit_paper, render_audit, render_outline

PAPER_PIPELINE_PY = Path(__file__).resolve().parent.parent / "scripts" / "paper_pipeline.py"


def test_audit_paper_flags_placeholders_ai_phrases_and_weak_captions(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text(
        "# Draft\n\n"
        "## Introduction\n\n"
        "It is worth noting that this paper provides valuable insights. "
        "Following Author (YYYY), our estimates robustly demonstrate a causal effect.\n\n"
        "Table 1. Results\n",
        encoding="utf-8",
    )

    result = audit_paper(draft)
    checks = {item.id: item for item in result.checks}

    assert not checks["citation.placeholders"].passed
    assert not checks["writing.anti_ai_phrases"].passed
    assert not checks["writing.causal_overclaim"].passed
    assert not checks["caption.quality"].passed


def test_audit_paper_rewards_complete_concrete_draft(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text(
        "# Minimum Wage and Youth Employment\n\n"
        "## Abstract\n\n"
        "This draft reports a city-year DiD design and states estimates after data cleaning.\n\n"
        "## Introduction\n\n"
        "The central contribution is to estimate how staggered minimum-wage changes affect "
        "youth employment using city-year panel data.\n\n"
        "## Data\n\n"
        "The sample uses city-year observations, city identifiers, and yearly policy timing.\n\n"
        "## Empirical Strategy\n\n"
        "The identification argument relies on parallel trends and city-clustered inference.\n\n"
        "## Results\n\n"
        "Table 1. Baseline DiD estimates for youth employment, city-year sample, clustered by city.\n\n"
        "## Robustness\n\n"
        "Figure 1. Event-study estimates with 95 percent confidence intervals around the policy year.\n\n"
        "## References\n\n"
        "Card, D. and Krueger, A. 1994. Minimum Wages and Employment.\n",
        encoding="utf-8",
    )

    result = audit_paper(draft)

    assert result.score >= 8
    assert not [item for item in result.checks if item.severity == "critical" and not item.passed]


def test_audit_paper_recognizes_journal_numbered_headings(tmp_path):
    draft = tmp_path / "journal_draft.md"
    draft.write_text(
        "# I. Introduction\n\n"
        "The contribution is narrow and testable: the paper links communication distance to repricing magnitude.\n\n"
        "# IV. Data\n\n"
        "The sample is a currency-tenor event panel.\n\n"
        "# VII. Empirical Strategy\n\n"
        "The model uses fixed effects and clustered inference.\n\n"
        "# VIII. Results\n\n"
        "Table 1. Main estimates for the event-panel sample with two-way clustered standard errors.\n\n"
        "# X. Robustness and Inference\n\n"
        "Figure 1. Sensitivity of the main coefficient across inference choices and event windows.\n\n"
        "# References\n\n"
        "Du, Tepper, and Verdelhan. 2018.\n",
        encoding="utf-8",
    )

    checks = {item.id: item for item in audit_paper(draft).checks}

    assert checks["paper.core_sections"].passed
    assert checks["paper.contribution_sentence"].passed


def test_render_outline_uses_brief_without_fabricating_sources(tmp_path):
    brief = {
        "question": "最低工资调整对青年就业率的因果效应是什么？",
        "contribution": "使用城市-年份面板估计错时政策调整。",
        "identification_seed": "DiD",
        "target_journal": "CSSCI",
        "data": {"unit_id": "city_id", "time_id": "year", "outcome": "youth_employment_rate"},
    }

    outline = render_outline(brief)

    assert "最低工资调整" in outline
    assert "DiD" in outline
    assert "[待核验来源]" in outline
    assert "Author (YYYY)" not in outline


def test_render_audit_includes_scope_note_for_citation_truth(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text("## Introduction\n\nNo references yet.\n", encoding="utf-8")

    report = render_audit(audit_paper(draft))

    assert "# Paper Quality Audit" in report
    assert "does not verify that cited sources exist" in report


def test_paper_pipeline_cli_audit_json_is_parseable(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text("## Introduction\n\nFollowing Author (YYYY).\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(PAPER_PIPELINE_PY),
            "audit",
            "--paper",
            str(draft),
            "--json",
            "--fail-under",
            "9",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 2
    data = json.loads(proc.stdout)
    assert data["paper_path"].endswith("draft.md")
    assert any(item["id"] == "citation.placeholders" for item in data["checks"])


def test_paper_pipeline_cli_outline_writes_markdown(tmp_path):
    brief = tmp_path / "brief.yaml"
    out_file = tmp_path / "outline.md"
    brief.write_text(
        "question: 最低工资调整对青年就业率的因果效应是什么？\n"
        "contribution: 使用城市-年份面板估计错时政策调整。\n"
        "identification_seed: DiD\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(PAPER_PIPELINE_PY),
            "outline",
            "--brief",
            str(brief),
            "--output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 0
    assert out_file.exists()
    assert "Paper Outline" in out_file.read_text(encoding="utf-8")
