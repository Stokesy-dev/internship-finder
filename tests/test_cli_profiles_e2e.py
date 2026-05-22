from __future__ import annotations

from pathlib import Path
import pytest

from src.config import AgentSettings
from src.internship_scraper import InternshipScraper
from src.main import settings_from_args
from src.pipeline import InternshipIntelligenceAgent


FIXTURES = Path(__file__).parent / "fixtures"


def _settings(command: str, tmp_path: Path, resume_pdf: Path) -> AgentSettings:
    import argparse

    from src.main import build_parser

    args = build_parser().parse_args(
        [
            command,
            "--resume",
            str(resume_pdf),
            "--jobs-csv",
            str(FIXTURES / "internships.csv"),
            "--no-llm",
            "--no-embeddings",
            "--reports-dir",
            str(tmp_path / "reports"),
            "--top-k",
            "3",
        ]
    )
    return settings_from_args(args)


@pytest.fixture
def resume_pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "resume.pdf"
    try:
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), (FIXTURES / "resume.txt").read_text(encoding="utf-8"))
        doc.save(pdf)
        doc.close()
    except ImportError:
        pytest.skip("PyMuPDF required for PDF fixture")
    return pdf


def test_discover_command_writes_reports(tmp_path: Path, resume_pdf: Path) -> None:
    settings = _settings("discover", tmp_path, resume_pdf)
    assert settings.filter_mode == "lenient"
    result = InternshipIntelligenceAgent(settings).run()
    assert result.ranked
    assert result.report_paths["top_internships"].exists()


def test_shortlist_uses_stricter_filter_than_discover() -> None:
    from src.models import Internship

    listing = Internship(
        title="Machine Learning Intern",
        company="Co",
        location="Remote India",
        description="machine learning intern Python TensorFlow remote India",
        stipend_inr=0,
        duration_months=0,
        apply_url="https://example.com/x",
        source="test",
    )
    lenient = InternshipScraper(filter_mode="lenient").filter_internships([listing])
    strict = InternshipScraper(filter_mode="strict").filter_internships([listing])
    assert len(lenient) == 1
    assert len(strict) == 0


def test_shortlist_command_writes_reports(tmp_path: Path, resume_pdf: Path) -> None:
    settings = _settings("shortlist", tmp_path, resume_pdf)
    assert settings.filter_mode == "strict"
    result = InternshipIntelligenceAgent(settings).run()
    assert result.ranked
    assert result.report_paths["top_internships"].exists()
