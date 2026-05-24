"""identify_strategy.py 测试 —— 决策树打分逻辑。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from identify_strategy import (
    Strategy,
    evaluate_strategies,
    load_brief,
    render_report,
)


# --- 数据类 ---------------------------------------------------------------

def test_strategy_dataclass_defaults():
    s = Strategy(name="X", chinese="测试")
    assert s.score == 0.0
    assert s.rationale == []
    assert s.references == []
    assert s.statspai_funcs == []
    assert s.robustness_must == []
    assert s.pitfalls == []


# --- evaluate_strategies -------------------------------------------------

def test_evaluate_returns_list_of_strategies():
    brief = {"data": {"structure": "panel"}}
    out = evaluate_strategies(brief)
    assert isinstance(out, list)
    assert all(isinstance(s, Strategy) for s in out)
    assert len(out) >= 5    # 至少 DiD / RDD / IV / SCM / Matching / DML


def test_evaluate_sorted_descending_by_score():
    brief = {
        "data": {"structure": "panel"},
        "identification_seed": "DiD",
    }
    out = evaluate_strategies(brief)
    scores = [s.score for s in out]
    assert scores == sorted(scores, reverse=True)


def test_evaluate_includes_all_main_strategies():
    out = evaluate_strategies({"data": {"structure": "panel"}})
    names = {s.name for s in out}
    expected = {"DiD", "RDD", "IV", "SCM", "Matching", "DML"}
    assert expected.issubset(names)


# --- DiD 决策树规则 ------------------------------------------------------

def test_did_panel_data_scored_higher():
    panel = evaluate_strategies({"data": {"structure": "panel"}})
    cross = evaluate_strategies({"data": {"structure": "cross_section"}})
    did_panel = next(s for s in panel if s.name == "DiD")
    did_cross = next(s for s in cross if s.name == "DiD")
    assert did_panel.score > did_cross.score


def test_did_natural_experiment_boost():
    out = evaluate_strategies({
        "data": {"structure": "panel"},
        "natural_experiment": "2018 reform shocked listed firms",
    })
    did = next(s for s in out if s.name == "DiD")
    assert did.score > 30   # natural exp + panel 至少应该叠加几个加分项


def test_did_seed_matches_chinese_keyword():
    out = evaluate_strategies({
        "data": {"structure": "panel"},
        "identification_seed": "双重差分",
    })
    did = next(s for s in out if s.name == "DiD")
    assert any("DiD" in r or "双重差分" in r or "panel" in r.lower() for r in did.rationale)
    # 用户 seed = DiD → DiD 应该是第一
    assert out[0].name == "DiD"


# --- RDD 决策树规则 -------------------------------------------------------

def test_rdd_cutoff_keyword_boost():
    out = evaluate_strategies({
        "data": {"structure": "cross_section"},
        "identification_seed": "cutoff at 60 score",
    })
    rdd = next(s for s in out if s.name == "RDD")
    assert rdd.score >= 80
    assert out[0].name == "RDD"


def test_rdd_chinese_keyword():
    out = evaluate_strategies({
        "identification_seed": "断点回归",
    })
    rdd = next(s for s in out if s.name == "RDD")
    assert rdd.score >= 80


def test_rdd_exam_score_context_boost():
    out = evaluate_strategies({
        "identification_seed": "rdd",
        "confounders": ["test score manipulation"],
    })
    rdd = next(s for s in out if s.name == "RDD")
    # cutoff(80) + test(20) = 100
    assert rdd.score >= 90


# --- IV 决策树规则 -------------------------------------------------------

def test_iv_seed_boost():
    out = evaluate_strategies({
        "identification_seed": "IV with rainfall",
    })
    iv = next(s for s in out if s.name == "IV")
    assert iv.score >= 60


def test_iv_reverse_causality_boost():
    out = evaluate_strategies({
        "identification_seed": "iv",
        "confounders": ["反向因果"],
    })
    iv = next(s for s in out if s.name == "IV")
    # seed (60) + reverse causality (20) = 80
    assert iv.score >= 80


def test_iv_candidates_boost():
    out = evaluate_strategies({
        "identification_seed": "iv",
        "data": {"iv_candidates": ["rainfall", "distance to capital"]},
    })
    iv = next(s for s in out if s.name == "IV")
    # seed (60) + candidates (20) = 80
    assert iv.score >= 80


# --- SCM 决策树规则 ------------------------------------------------------

def test_scm_panel_boost():
    out = evaluate_strategies({
        "identification_seed": "SCM",
        "data": {"structure": "panel"},
    })
    scm = next(s for s in out if s.name == "SCM")
    # seed 70 + panel 30 = 100
    assert scm.score >= 100


def test_scm_province_granularity_boost():
    out = evaluate_strategies({
        "identification_seed": "scm",
        "data": {"structure": "panel", "granularity": "province"},
    })
    scm = next(s for s in out if s.name == "SCM")
    # seed 70 + panel 30 + province 20 = 120
    assert scm.score >= 120


def test_scm_chinese_keyword():
    out = evaluate_strategies({"identification_seed": "合成控制"})
    scm = next(s for s in out if s.name == "SCM")
    assert scm.score >= 70


# --- Matching 决策树 ----------------------------------------------------

def test_matching_downweighted():
    """学术界共识：Matching 弱于 DiD/RDD/IV，全局 -10。"""
    out = evaluate_strategies({"identification_seed": "matching"})
    matching = next(s for s in out if s.name == "Matching")
    # seed 60 - global -10 = 50
    assert matching.score <= 60


def test_matching_does_not_go_negative():
    """全局 -10 不应让无相关信号的 Matching 评分变负。"""
    out = evaluate_strategies({"data": {"structure": "panel"}})
    matching = next(s for s in out if s.name == "Matching")
    assert matching.score >= 0


# --- DML 决策树规则 -----------------------------------------------------

def test_dml_ml_keyword_boost():
    out = evaluate_strategies({"identification_seed": "DML with random forest"})
    dml = next(s for s in out if s.name == "DML")
    assert dml.score >= 60


def test_dml_high_dim_controls_boost():
    controls = [f"control_{i}" for i in range(15)]
    out = evaluate_strategies({
        "identification_seed": "dml",
        "data": {"controls": controls},
    })
    dml = next(s for s in out if s.name == "DML")
    # seed 60 + high-dim 15 = 75
    assert dml.score >= 75


# --- 完整 brief 集成 ----------------------------------------------------

def test_full_did_brief_picks_did_as_top1():
    brief = {
        "question": "Does AI adoption increase firm productivity?",
        "data": {"structure": "panel", "granularity": "firm",
                 "sample_size": "large"},
        "identification_seed": "DiD",
        "natural_experiment": "AI policy released 2020",
    }
    out = evaluate_strategies(brief)
    assert out[0].name == "DiD"


def test_full_rdd_brief_picks_rdd_as_top1():
    brief = {
        "question": "Does college admission affect earnings?",
        "data": {"structure": "cross_section"},
        "identification_seed": "RDD around 60 cutoff score",
        "confounders": ["exam score manipulation"],
    }
    out = evaluate_strategies(brief)
    assert out[0].name == "RDD"


def test_full_iv_brief_picks_iv_as_top1():
    brief = {
        "data": {"iv_candidates": ["rainfall_shock"]},
        "identification_seed": "IV approach",
        "confounders": ["反向因果"],
    }
    out = evaluate_strategies(brief)
    # IV (60+20+20=100) 应该胜过 DiD/Matching 等
    assert out[0].name == "IV"


# --- load_brief ---------------------------------------------------------

def test_load_brief_from_json(tmp_path):
    p = tmp_path / "brief.json"
    p.write_text(json.dumps({"question": "test", "data": {"structure": "panel"}}),
                 encoding="utf-8")
    brief = load_brief(p)
    assert brief["question"] == "test"


def test_load_brief_from_yaml(tmp_path):
    pytest.importorskip("yaml")
    p = tmp_path / "brief.yaml"
    p.write_text("question: test\ndata:\n  structure: panel\n",
                 encoding="utf-8")
    brief = load_brief(p)
    assert brief["question"] == "test"
    assert brief["data"]["structure"] == "panel"


# --- render_report -------------------------------------------------------

def test_render_report_includes_summary():
    brief = {
        "question": "X causes Y",
        "data": {"structure": "panel", "granularity": "firm"},
        "identification_seed": "DiD",
    }
    out = evaluate_strategies(brief)
    text = render_report(brief, out, top_k=3)
    assert "## Brief Summary" in text
    assert "X causes Y" in text
    assert "## Top 3 Recommendations" in text


def test_render_report_uses_top_k():
    brief = {"data": {"structure": "panel"}}
    out = evaluate_strategies(brief)
    text = render_report(brief, out, top_k=2)
    # 应该有 #1 和 #2 但没有 #4
    assert "#1:" in text
    assert "#2:" in text
    assert "#4:" not in text


def test_render_report_truncates_long_rationale():
    """rationale 太长时表格里截断 80 字符。"""
    s = Strategy(name="DiD", chinese="双重差分", score=100,
                 rationale=["很长的理由 " * 30])
    text = render_report({}, [s], top_k=1)
    # 表格行不应包含全部 30 次重复
    table_line = [l for l in text.split("\n") if "DiD" in l and "100" in l][0]
    assert len(table_line) < 400


def test_render_report_no_strategies():
    text = render_report({}, [], top_k=3)
    assert "## Top 3 Recommendations" in text


def test_render_report_markdown_links():
    """检查表格 + 章节 + checklist 等 markdown 元素都在。"""
    brief = {"data": {"structure": "panel"}}
    out = evaluate_strategies(brief)
    text = render_report(brief, out, top_k=2)
    assert "**Robustness checks (mandatory)**" in text
    assert "**Key references**:" in text
    assert "- [ ]" in text   # checklist
