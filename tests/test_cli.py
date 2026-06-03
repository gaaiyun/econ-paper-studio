"""cli.py 测试 —— 子命令分发器。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cli import (
    ALIASES,
    PROJECT_ROOT,
    SCRIPT_DIR,
    SUBCOMMANDS,
    banner,
    main,
    open_doc,
)

CLI_PY = SCRIPT_DIR / "cli.py"


# --- 常量 ---------------------------------------------------------------

def test_script_dir_points_to_scripts():
    assert SCRIPT_DIR.name == "scripts"


def test_project_root_above_scripts():
    assert (PROJECT_ROOT / "scripts").is_dir()


def test_subcommands_dict_keys():
    expected = {"doctor", "identify", "scaffold", "session", "init", "list",
                "show", "add", "promote", "verify"}
    assert expected <= set(SUBCOMMANDS.keys())


def test_session_shortcuts_dispatch_to_session_py():
    """init / list / show / add / promote 都应该最终走 session.py。"""
    for k in ("init", "list", "show", "add", "promote"):
        target = SUBCOMMANDS[k]
        assert isinstance(target, tuple)
        assert target[0] == "session.py"


def test_aliases_resolve_to_real_commands():
    """所有 alias 的目标都应该是 valid 命令。"""
    valid_cmds = set(SUBCOMMANDS.keys()) | {"brainstorm", "workflow"}
    for alias, target in ALIASES.items():
        assert target in valid_cmds, f"alias {alias} → {target} 不是 valid 命令"


def test_banner_is_ascii_safe_for_windows_console(capsys):
    banner()
    out = capsys.readouterr().out
    assert out.isascii()
    assert "doctor" in out
    assert "verify" in out


# --- banner / open_doc -------------------------------------------------

def test_banner_runs_without_error(capsys):
    banner()
    out = capsys.readouterr().out
    assert "econ-paper-studio" in out
    assert "brainstorm" in out


def test_open_doc_reads_existing_file(capsys):
    code = open_doc("README.md")
    assert code == 0
    out = capsys.readouterr().out
    assert "README.md location" in out
    assert PROJECT_ROOT.name in out


def test_open_doc_missing_file(capsys):
    code = open_doc("nonexistent_file_12345.md")
    assert code == 1
    err = capsys.readouterr().err
    assert "not found" in err


# --- main 入口分发 -----------------------------------------------------

def test_main_no_args_prints_banner(capsys):
    with patch.object(sys, "argv", ["cli.py"]):
        code = main()
    assert code == 0
    assert "econ-paper-studio" in capsys.readouterr().out


def test_main_help_prints_banner(capsys):
    with patch.object(sys, "argv", ["cli.py", "--help"]):
        code = main()
    assert code == 0


def test_main_help_short(capsys):
    with patch.object(sys, "argv", ["cli.py", "-h"]):
        code = main()
    assert code == 0


def test_main_brainstorm_opens_research_question(capsys):
    with patch.object(sys, "argv", ["cli.py", "brainstorm"]):
        code = main()
    assert code == 0
    assert "RESEARCH_QUESTION.md" in capsys.readouterr().out


def test_main_workflow_opens_workflow_md(capsys):
    with patch.object(sys, "argv", ["cli.py", "workflow"]):
        code = main()
    assert code == 0
    assert "WORKFLOW.md" in capsys.readouterr().out


def test_main_alias_b_routes_to_brainstorm(capsys):
    with patch.object(sys, "argv", ["cli.py", "b"]):
        code = main()
    assert code == 0
    assert "RESEARCH_QUESTION.md" in capsys.readouterr().out


def test_main_alias_w_routes_to_workflow(capsys):
    with patch.object(sys, "argv", ["cli.py", "w"]):
        code = main()
    assert code == 0


def test_main_unknown_command_returns_2(capsys):
    with patch.object(sys, "argv", ["cli.py", "bogus_command_xyz"]):
        code = main()
    assert code == 2
    assert "Unknown subcommand" in capsys.readouterr().err


# --- 子进程级端到端 -----------------------------------------------------

def _run_cli(args, cwd=None):
    cmd = [sys.executable, str(CLI_PY), *args]
    return subprocess.run(cmd, cwd=cwd or PROJECT_ROOT,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def test_cli_subprocess_banner():
    proc = _run_cli([])
    assert proc.returncode == 0
    assert "econ-paper-studio" in proc.stdout


def test_cli_subprocess_identify_help():
    proc = _run_cli(["identify", "--help"])
    assert proc.returncode == 0
    assert "brief" in proc.stdout.lower() or "interactive" in proc.stdout.lower()


def test_cli_subprocess_scaffold_help():
    proc = _run_cli(["scaffold", "--help"])
    assert proc.returncode == 0
    assert "strategy" in proc.stdout.lower()


def test_cli_subprocess_verify_help():
    proc = _run_cli(["verify", "--help"])
    assert proc.returncode == 0
    assert "analysis" in proc.stdout.lower()


def test_cli_subprocess_doctor_json():
    proc = _run_cli(["doctor", "--json"])
    assert proc.returncode == 0
    assert '"checks"' in proc.stdout
    assert '"python_version"' in proc.stdout


def test_cli_subprocess_session_list_in_empty_dir(tmp_path):
    proc = _run_cli(["list"], cwd=tmp_path)
    # session list 在没有 outputs/ 的目录跑应该返回 0 + 提示
    assert proc.returncode == 0
    assert "no sessions" in proc.stdout.lower()


def test_cli_aliases_short_forms(tmp_path):
    """sc 是 scaffold 的别名，--help 应被透传。"""
    proc = _run_cli(["sc", "--help"])
    assert proc.returncode == 0
    assert "strategy" in proc.stdout.lower()


def test_cli_verify_alias_short_form():
    proc = _run_cli(["v", "--help"])
    assert proc.returncode == 0
    assert "analysis" in proc.stdout.lower()
