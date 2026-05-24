"""session.py 测试 —— 论文 session 生命周期 CRUD。"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from session import (
    DEFAULT_BASE,
    changelog_path,
    cmd_add,
    cmd_add_review,
    cmd_init,
    cmd_list,
    cmd_promote,
    cmd_show,
    manifest_path,
    session_dir,
)


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return tmp_path / "outputs"


# --- helpers ----------------------------------------------------------------

def _init_args(base: Path, name: str = "test-paper", **kwargs) -> SimpleNamespace:
    defaults = {
        "base_dir": str(base),
        "name": name,
        "rq": "X causes Y in setting Z",
        "strategy": "DiD",
        "target_journal": "",
        "data_source": "",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _add_args(base: Path, name: str, **kwargs) -> SimpleNamespace:
    defaults = {
        "base_dir": str(base), "name": name,
        "version": "v1", "paper": None, "note": "first draft",
        "score": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# --- session_dir / manifest_path / changelog_path -------------------------

def test_session_dir_constructs_path(tmp_path):
    out = session_dir(tmp_path / "outputs", "my-paper")
    assert out == tmp_path / "outputs" / "my-paper"


def test_manifest_path_appends_manifest_json(tmp_path):
    assert manifest_path(tmp_path).name == "manifest.json"


def test_changelog_path_appends_changelog_md(tmp_path):
    assert changelog_path(tmp_path).name == "CHANGELOG.md"


def test_default_base_is_outputs():
    assert str(DEFAULT_BASE) == "outputs"


# --- cmd_init -------------------------------------------------------------

def test_init_creates_session_dir(base):
    code = cmd_init(_init_args(base))
    assert code == 0
    assert session_dir(base, "test-paper").is_dir()


def test_init_creates_subdirs(base):
    cmd_init(_init_args(base))
    s_dir = session_dir(base, "test-paper")
    expected_subs = {"data", "do", "R", "tables", "figures",
                     "robustness", "paper", "paper/v1", "referee_response"}
    for sub in expected_subs:
        assert (s_dir / sub).is_dir(), f"缺子目录 {sub}"


def test_init_writes_manifest_with_metadata(base):
    cmd_init(_init_args(base, target_journal="JPE", data_source="CSMAR"))
    m = json.loads(manifest_path(session_dir(base, "test-paper")).read_text(encoding="utf-8"))
    assert m["name"] == "test-paper"
    assert m["research_question"] == "X causes Y in setting Z"
    assert m["strategy"] == "DiD"
    assert m["target_journal"] == "JPE"
    assert m["data_source"] == "CSMAR"
    assert m["iterations"] == []
    assert m["reviews"] == []
    assert m["final_version"] is None


def test_init_writes_changelog(base):
    cmd_init(_init_args(base))
    cl = changelog_path(session_dir(base, "test-paper")).read_text(encoding="utf-8")
    assert "test-paper" in cl
    assert "X causes Y in setting Z" in cl
    assert "## Paper Iterations" in cl
    assert "## Referee Reviews" in cl


def test_init_rejects_duplicate(base, capsys):
    cmd_init(_init_args(base))
    code = cmd_init(_init_args(base))
    assert code == 1
    err = capsys.readouterr().err
    assert "already exists" in err


# --- cmd_list -------------------------------------------------------------

def test_list_empty_base(base, capsys):
    code = cmd_list(SimpleNamespace(base_dir=str(base)))
    assert code == 0
    out = capsys.readouterr().out
    assert "no sessions" in out.lower()


def test_list_after_init(base, capsys):
    cmd_init(_init_args(base, name="paper-a", strategy="DiD"))
    cmd_init(_init_args(base, name="paper-b", strategy="RDD"))
    cmd_list(SimpleNamespace(base_dir=str(base)))
    out = capsys.readouterr().out
    assert "paper-a" in out
    assert "paper-b" in out
    assert "DiD" in out
    assert "RDD" in out


def test_list_skips_dir_without_manifest(base, capsys):
    cmd_init(_init_args(base, name="valid"))
    # 加一个没 manifest 的"伪 session"
    (base / "fake").mkdir()
    cmd_list(SimpleNamespace(base_dir=str(base)))
    out = capsys.readouterr().out
    assert "valid" in out
    assert "fake" not in out


# --- cmd_show -------------------------------------------------------------

def test_show_valid_session(base, capsys):
    cmd_init(_init_args(base))
    code = cmd_show(SimpleNamespace(base_dir=str(base), name="test-paper"))
    assert code == 0
    out = capsys.readouterr().out
    assert "research_question" in out
    assert "X causes Y" in out
    assert "CHANGELOG.md" in out


def test_show_missing_session(base, capsys):
    code = cmd_show(SimpleNamespace(base_dir=str(base), name="nonexistent"))
    assert code == 1
    err = capsys.readouterr().err
    assert "not found" in err.lower()


# --- cmd_add --------------------------------------------------------------

def test_add_iteration_appends_to_manifest(base):
    cmd_init(_init_args(base))
    cmd_add(_add_args(base, "test-paper", version="v1", note="initial draft"))
    m = json.loads(manifest_path(session_dir(base, "test-paper")).read_text(encoding="utf-8"))
    assert len(m["iterations"]) == 1
    assert m["iterations"][0]["version"] == "v1"
    assert m["iterations"][0]["note"] == "initial draft"


def test_add_multiple_iterations(base):
    cmd_init(_init_args(base))
    cmd_add(_add_args(base, "test-paper", version="v1", note="first"))
    cmd_add(_add_args(base, "test-paper", version="v2", note="revised"))
    cmd_add(_add_args(base, "test-paper", version="v3", note="final"))
    m = json.loads(manifest_path(session_dir(base, "test-paper")).read_text(encoding="utf-8"))
    assert len(m["iterations"]) == 3
    versions = [it["version"] for it in m["iterations"]]
    assert versions == ["v1", "v2", "v3"]


def test_add_with_score(base):
    cmd_init(_init_args(base))
    cmd_add(_add_args(base, "test-paper", version="v1", note="x", score=7.5))
    m = json.loads(manifest_path(session_dir(base, "test-paper")).read_text(encoding="utf-8"))
    assert m["iterations"][0]["score"] == 7.5


def test_add_to_missing_session(base, capsys):
    code = cmd_add(_add_args(base, "nonexistent"))
    assert code == 1
    assert "not found" in capsys.readouterr().err.lower()


def test_add_updates_changelog(base):
    cmd_init(_init_args(base))
    cmd_add(_add_args(base, "test-paper", version="v1", note="initial draft"))
    cl = changelog_path(session_dir(base, "test-paper")).read_text(encoding="utf-8")
    # "_(none yet)_" 应被替换
    assert "_(none yet)_" not in cl.split("## Referee Reviews")[0]
    assert "### v1" in cl
    assert "initial draft" in cl


def test_add_with_paper_path(base, tmp_path):
    cmd_init(_init_args(base))
    paper_file = tmp_path / "draft.docx"
    paper_file.write_bytes(b"fake docx content")
    cmd_add(_add_args(base, "test-paper", version="v1",
                       paper=str(paper_file), note="x"))
    m = json.loads(manifest_path(session_dir(base, "test-paper")).read_text(encoding="utf-8"))
    assert m["iterations"][0]["paper"] == str(paper_file)


# --- cmd_add_review --------------------------------------------------------

def test_add_review_appends_to_manifest(base, tmp_path):
    cmd_init(_init_args(base))
    letter = tmp_path / "ref.txt"
    letter.write_text("Reviewer 1: ...")
    cmd_add_review(SimpleNamespace(
        base_dir=str(base), name="test-paper",
        version="r1", letter=str(letter), decision="major",
    ))
    m = json.loads(manifest_path(session_dir(base, "test-paper")).read_text(encoding="utf-8"))
    assert len(m["reviews"]) == 1
    assert m["reviews"][0]["version"] == "r1"
    assert m["reviews"][0]["decision"] == "major"


def test_add_review_missing_session(base, capsys):
    code = cmd_add_review(SimpleNamespace(
        base_dir=str(base), name="nonexistent",
        version="r1", letter="x.txt", decision=""))
    assert code == 1


def test_add_review_updates_changelog(base, tmp_path):
    cmd_init(_init_args(base))
    letter = tmp_path / "ref.txt"
    letter.write_text("x")
    cmd_add_review(SimpleNamespace(
        base_dir=str(base), name="test-paper",
        version="r1", letter=str(letter), decision="minor",
    ))
    cl = changelog_path(session_dir(base, "test-paper")).read_text(encoding="utf-8")
    assert "### r1" in cl
    assert "minor" in cl


# --- cmd_promote ----------------------------------------------------------

def test_promote_sets_final_version(base):
    cmd_init(_init_args(base))
    cmd_add(_add_args(base, "test-paper", version="v2", note="x"))
    code = cmd_promote(SimpleNamespace(
        base_dir=str(base), name="test-paper", version="v2"))
    assert code == 0
    m = json.loads(manifest_path(session_dir(base, "test-paper")).read_text(encoding="utf-8"))
    assert m["final_version"] == "v2"
    assert "promoted_at" in m


def test_promote_missing_version(base, capsys):
    cmd_init(_init_args(base))
    cmd_add(_add_args(base, "test-paper", version="v1", note="x"))
    code = cmd_promote(SimpleNamespace(
        base_dir=str(base), name="test-paper", version="v999"))
    assert code == 1
    assert "not found" in capsys.readouterr().err.lower()


def test_promote_copies_paper_to_final(base, tmp_path):
    cmd_init(_init_args(base))
    paper_file = tmp_path / "draft.docx"
    paper_file.write_bytes(b"final paper content")
    cmd_add(_add_args(base, "test-paper", version="v2",
                       paper=str(paper_file), note="x"))
    cmd_promote(SimpleNamespace(base_dir=str(base),
                                 name="test-paper", version="v2"))
    final = session_dir(base, "test-paper") / "paper" / "final.docx"
    assert final.exists()
    assert final.read_bytes() == b"final paper content"


def test_promote_changelog_marker(base):
    cmd_init(_init_args(base))
    cmd_add(_add_args(base, "test-paper", version="v2", note="x"))
    cmd_promote(SimpleNamespace(base_dir=str(base),
                                 name="test-paper", version="v2"))
    cl = changelog_path(session_dir(base, "test-paper")).read_text(encoding="utf-8")
    assert "PROMOTED" in cl
    assert "v2" in cl
