from __future__ import annotations

from pathlib import Path

import pytest

from src.config import AgentSettings
from src.filter_policy import FilterPolicy
from src.internship_scraper import InternshipScraper
from src.pipeline import InternshipIntelligenceAgent


FIXTURES = Path(__file__).parent / "fixtures"


def _write_resume_pdf(path: Path) -> None:
    try:
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), (FIXTURES / "resume.txt").read_text(encoding="utf-8"))
        doc.save(path)
        doc.close()
    except ImportError:
        from pypdf import PdfWriter

        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        # Minimal PDF without text layer still parses via pypdf empty; use fitz preferred.
        writer.add_metadata({})
        writer.write(path)


@pytest.fixture
def resume_pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "resume.pdf"
    _write_resume_pdf(pdf)
    return pdf


def test_lenient_scraper_accepts_zero_stipend_listing() -> None:
    scraper = InternshipScraper(filter_mode="lenient")
    from src.models import Internship

    listing = Internship(
        title="Machine Learning Intern",
        company="X",
        location="Remote India",
        description="machine learning intern Python TensorFlow remote India",
        stipend_inr=0,
        duration_months=0,
        apply_url="https://example.com/1",
        source="test",
    )
    filtered = scraper.filter_internships([listing])
    assert len(filtered) == 1


def test_lenient_pipeline_writes_reports(tmp_path: Path, resume_pdf: Path) -> None:
    reports_dir = tmp_path / "reports"
    settings = AgentSettings(
        resume_path=resume_pdf,
        jobs_csv=FIXTURES / "internships.csv",
        filter_mode="lenient",
        reports_dir=reports_dir,
        limit=10,
        top_k=3,
        use_llm=False,
        use_embeddings=False,
    )
    result = InternshipIntelligenceAgent(settings).run()
    assert result.ranked
    top_report = result.report_paths["top_internships"]
    assert top_report.exists()
    content = top_report.read_text(encoding="utf-8")
    assert "Machine Learning Intern" in content or "Data Science Intern" in content
    assert len(content) > 200


def test_strict_rejects_unknown_stipend() -> None:
    policy = FilterPolicy(mode="strict")
    from src.models import Internship

    listing = Internship(
        title="AI Intern",
        company="Y",
        location="India",
        description="artificial intelligence intern remote India Python",
        stipend_inr=0,
        duration_months=6,
        apply_url="https://example.com/2",
        source="test",
    )
    assert not policy.evaluate(listing).accepted
