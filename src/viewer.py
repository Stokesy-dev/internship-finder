from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPORT_FILES: dict[str, str] = {
    "top_internships": "top_internships.md",
    "skill_gap_analysis": "skill_gap_analysis.md",
    "learning_roadmaps": "learning_roadmaps.md",
    "interview_prep": "interview_prep.md",
    "application_strategy": "application_strategy.md",
}

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPLOADS_DIR = REPO_ROOT / "uploads"
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"


def find_resume_pdfs(uploads_dir: Path | None = None) -> list[Path]:
    directory = uploads_dir or DEFAULT_UPLOADS_DIR
    if not directory.exists():
        return []
    return sorted(directory.glob("*.pdf"))


def default_resume_path(uploads_dir: Path | None = None) -> Path | None:
    pdfs = find_resume_pdfs(uploads_dir)
    return pdfs[0] if pdfs else None


def load_reports(reports_dir: Path | None = None) -> dict[str, tuple[Path | None, str]]:
    directory = reports_dir or DEFAULT_REPORTS_DIR
    loaded: dict[str, tuple[Path | None, str]] = {}
    for key, filename in REPORT_FILES.items():
        path = directory / filename
        if path.is_file():
            loaded[key] = (path, path.read_text(encoding="utf-8"))
        else:
            loaded[key] = (None, "")
    return loaded


def build_agent_argv(
    command: str,
    resume_path: Path,
    *,
    role_query: str = "",
    reports_dir: Path | None = None,
    jobs_csv: Path | None = None,
    no_llm: bool = False,
    no_embeddings: bool = False,
) -> list[str]:
    if command not in {"discover", "shortlist"}:
        raise ValueError(f"Unknown command: {command!r}")

    resume = Path(resume_path).expanduser().resolve()
    if not resume.is_file():
        raise FileNotFoundError(f"Resume not found: {resume}")

    argv = [
        sys.executable,
        str(REPO_ROOT / "main.py"),
        command,
        "--resume",
        str(resume),
    ]
    if role_query.strip():
        argv.extend(["--role", role_query.strip()])
    if reports_dir is not None:
        argv.extend(["--reports-dir", str(Path(reports_dir).resolve())])
    if jobs_csv is not None and Path(jobs_csv).is_file():
        argv.extend(["--jobs-csv", str(Path(jobs_csv).resolve())])
    if no_llm:
        argv.append("--no-llm")
    if no_embeddings:
        argv.append("--no-embeddings")
    return argv


def run_agent(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: int = 3600,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
