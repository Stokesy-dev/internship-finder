from __future__ import annotations

from pathlib import Path

import pytest

from src.viewer import (
    REPORT_FILES,
    build_agent_argv,
    default_resume_path,
    find_resume_pdfs,
    load_reports,
    REPO_ROOT,
)


def test_report_files_cover_five_outputs() -> None:
    assert len(REPORT_FILES) == 5
    assert "top_internships" in REPORT_FILES


def test_find_resume_pdfs_in_uploads() -> None:
    pdfs = find_resume_pdfs(REPO_ROOT / "uploads")
    assert any(p.name.endswith(".pdf") for p in pdfs)


def test_default_resume_path_prefers_uploads() -> None:
    resume = default_resume_path(REPO_ROOT / "uploads")
    if resume:
        assert resume.parent.name == "uploads"


def test_load_reports_reads_existing_files(tmp_path: Path) -> None:
    (tmp_path / "top_internships.md").write_text("# Top\n\n- One", encoding="utf-8")
    reports = load_reports(tmp_path)
    assert "One" in reports["top_internships"][1]
    assert reports["skill_gap_analysis"][0] is None


def test_build_agent_argv_discover() -> None:
    resume = REPO_ROOT / "tests" / "fixtures" / "resume.pdf"
    if not resume.is_file():
        pytest.skip("resume fixture missing")
    argv = build_agent_argv("discover", resume, role_query="ml intern", no_llm=True)
    assert argv[2] == "discover"
    assert "--resume" in argv
    assert "--role" in argv
    assert "--no-llm" in argv


def test_build_agent_argv_rejects_missing_resume(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_agent_argv("shortlist", tmp_path / "missing.pdf")


def test_build_agent_argv_rejects_unknown_command() -> None:
    resume = REPO_ROOT / "tests" / "fixtures" / "resume.pdf"
    if not resume.is_file():
        pytest.skip("resume fixture missing")
    with pytest.raises(ValueError):
        build_agent_argv("rank", resume)


def test_streamlit_app_module_imports() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "streamlit_app",
        REPO_ROOT / "streamlit_app.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
