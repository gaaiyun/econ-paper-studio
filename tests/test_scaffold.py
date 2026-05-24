"""scaffold.py 测试 —— Stata / R 模板渲染。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scaffold import (
    R_TEMPLATES,
    STATA_TEMPLATES,
    write_files,
)


SCAFFOLD_PY = Path(__file__).resolve().parent.parent / "scripts" / "scaffold.py"


# --- 模板字典 -----------------------------------------------------------

def test_stata_templates_has_did():
    assert "DiD" in STATA_TEMPLATES
    assert isinstance(STATA_TEMPLATES["DiD"], dict)
    assert len(STATA_TEMPLATES["DiD"]) >= 6   # 至少 6 个标准 .do


def test_stata_templates_has_rdd():
    assert "RDD" in STATA_TEMPLATES


def test_stata_did_includes_six_master_files():
    files = STATA_TEMPLATES["DiD"]
    expected = {
        "00_master.do", "01_clean.do", "02_descriptive.do",
        "03_main.do", "04_robustness.do", "05_heterogeneity.do",
        "99_export.do",
    }
    assert expected <= set(files.keys())


def test_stata_master_lists_correct_subfiles():
    master = STATA_TEMPLATES["DiD"]["00_master.do"]
    for f in ("01_clean", "02_descriptive", "03_main",
              "04_robustness", "99_export"):
        assert f in master


def test_r_templates_has_did():
    assert "DiD" in R_TEMPLATES
    assert isinstance(R_TEMPLATES["DiD"], dict)


def test_templates_use_format_placeholders():
    """模板必须含 {session} 和 {ts} 占位符。"""
    for files in STATA_TEMPLATES["DiD"].values():
        # 至少 master 应该有 {session}
        if "master" in str(files).lower():
            assert "{session}" in files or "{ts}" in files


# --- write_files ------------------------------------------------------

def test_write_files_creates_all(tmp_path):
    files = {"a.do": "* paper {session} at {ts}", "b.do": "use data.dta"}
    written = write_files(tmp_path, files, session="mypaper", ts="2024-01-01")
    assert len(written) == 2
    assert (tmp_path / "a.do").exists()
    assert (tmp_path / "b.do").exists()


def test_write_files_substitutes_session_ts(tmp_path):
    files = {"x.do": "session={session}, time={ts}"}
    write_files(tmp_path, files, session="paper-1", ts="2024-01-01")
    content = (tmp_path / "x.do").read_text(encoding="utf-8")
    assert "session=paper-1" in content
    assert "time=2024-01-01" in content


def test_write_files_creates_subdirs(tmp_path):
    """如果模板 key 含 / 应自动建子目录。"""
    files = {"sub/nested.do": "* test"}
    write_files(tmp_path, files, session="x", ts="t")
    assert (tmp_path / "sub" / "nested.do").exists()


def test_write_files_handles_empty(tmp_path):
    written = write_files(tmp_path, {}, session="x", ts="t")
    assert written == []


# --- 模板内容质量 ------------------------------------------------------

def test_stata_did_main_includes_keyf_regression():
    """主回归必须含 reghdfe 或 did 命令。"""
    main = STATA_TEMPLATES["DiD"]["03_main.do"]
    assert "reghdfe" in main or "xtreg" in main or "did" in main.lower()


def test_stata_did_robustness_mentions_event_study():
    """稳健性应包含事件研究。"""
    rob = STATA_TEMPLATES["DiD"]["04_robustness.do"]
    # 包含至少一个：event study / 安慰剂 / Bacon
    lower = rob.lower()
    assert any(kw in lower for kw in ["event", "placebo", "bacon", "随机", "安慰剂"])


def test_stata_rdd_includes_rdrobust():
    """RDD 模板应调 rdrobust。"""
    rdd_files = STATA_TEMPLATES["RDD"]
    found = any("rdrobust" in f for f in rdd_files.values())
    assert found


def test_r_did_uses_event_study_or_callaway():
    """R DiD 模板应至少包含 event study 或 Callaway-Sant'Anna 工具。"""
    r_files = R_TEMPLATES["DiD"]
    all_content = "\n".join(r_files.values()).lower()
    assert any(kw in all_content for kw in ["did2s", "att_gt", "event", "fixest"])


# --- CLI 端到端 ------------------------------------------------------

def _run_scaffold(args, cwd):
    """跑 scaffold.py 作为子进程，返回 (returncode, stdout, stderr)。"""
    cmd = [sys.executable, str(SCAFFOLD_PY), *args]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout, proc.stderr


def test_cli_did_stata_creates_files(tmp_path):
    code, out, err = _run_scaffold(
        ["--strategy", "DiD", "--session", "test-paper",
         "--lang", "stata", "--output-dir", str(tmp_path)],
        cwd=tmp_path)
    assert code == 0, err
    out_dir = tmp_path / "test-paper" / "do"
    assert out_dir.is_dir()
    assert (out_dir / "00_master.do").exists()
    # 检查 substitution
    master = (out_dir / "00_master.do").read_text(encoding="utf-8")
    assert "test-paper" in master


def test_cli_did_r_creates_files(tmp_path):
    code, out, err = _run_scaffold(
        ["--strategy", "DiD", "--session", "test-paper",
         "--lang", "r", "--output-dir", str(tmp_path)],
        cwd=tmp_path)
    assert code == 0, err
    out_dir = tmp_path / "test-paper" / "R"
    assert out_dir.is_dir()


def test_cli_python_lang_not_implemented(tmp_path):
    code, out, err = _run_scaffold(
        ["--strategy", "DiD", "--session", "x",
         "--lang", "python", "--output-dir", str(tmp_path)],
        cwd=tmp_path)
    assert code == 1
    assert "not yet implemented" in err.lower()


def test_cli_unknown_strategy_fails(tmp_path):
    code, _, err = _run_scaffold(
        ["--strategy", "PSM", "--session", "x",
         "--lang", "stata", "--output-dir", str(tmp_path)],
        cwd=tmp_path)
    assert code == 1
    # PSM 在 choices 里但没模板（STATA_TEMPLATES 只有 DiD + RDD）
    assert "No template" in err or "no template" in err.lower()


def test_cli_creates_session_subdirs(tmp_path):
    """scaffold 应自动建 data/tables/figures/robustness 子目录。"""
    _run_scaffold(
        ["--strategy", "DiD", "--session", "test-paper",
         "--lang", "stata", "--output-dir", str(tmp_path)],
        cwd=tmp_path)
    session = tmp_path / "test-paper"
    for sub in ("data", "tables", "figures", "robustness"):
        assert (session / sub).is_dir(), f"缺 {sub}"


def test_cli_help_works(tmp_path):
    code, out, err = _run_scaffold(["--help"], cwd=tmp_path)
    assert code == 0
    assert "strategy" in out.lower()
    assert "session" in out.lower()
