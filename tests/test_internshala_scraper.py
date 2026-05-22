from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.filter_policy import FilterPolicy
from src.internship_scraper import InternshipScraper
from src.internshala_scraper import (
    InternshalaScraper,
    parse_internshala_listing_html,
)

FIXTURE = Path(__file__).parent / "fixtures" / "internshala_search.html"


def test_parse_fixture_extracts_internshala_rows() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    rows = parse_internshala_listing_html(html)
    assert len(rows) >= 2
    assert all(item.source == "internshala" for item in rows)
    assert all(item.title for item in rows)
    assert all(item.company for item in rows)


def test_parse_fixture_stipend_and_duration_when_present() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    rows = parse_internshala_listing_html(html)
    with_stipend = [r for r in rows if r.stipend_inr > 0]
    with_duration = [r for r in rows if r.duration_months > 0]
    assert with_stipend, "expected at least one parsed stipend from fixture"
    assert with_duration, "expected at least one parsed duration from fixture"
    india_cities = ("hyderabad", "bangalore", "mumbai", "india", "kolkata", "remote")
    assert any(
        any(city in f"{r.location} {r.description}".lower() for city in india_cities)
        for r in rows
    )


def test_internshala_failure_does_not_break_discovery() -> None:
    from src.models import Internship

    scraper = InternshipScraper(filter_mode="lenient", live_only=True)
    greenhouse_row = Internship(
        title="Machine Learning Intern",
        company="Test",
        location="Remote India",
        description="machine learning intern Python TensorFlow India remote",
        stipend_inr=25_000,
        duration_months=6,
        apply_url="https://example.com/g",
        source="greenhouse",
    )
    with patch.object(InternshipScraper, "_discover_manual_urls", return_value=[]):
        with patch.object(scraper.internshala, "discover", side_effect=RuntimeError("blocked")):
            with patch.object(scraper.greenhouse, "discover", return_value=[greenhouse_row]):
                with patch.object(scraper.lever, "discover", return_value=[]):
                    with patch.object(scraper.wellfound, "discover", return_value=[]):
                        with patch.object(scraper.company_careers, "discover", return_value=[]):
                            found = scraper.discover(limit=10)
    assert any(item.source == "greenhouse" for item in found)


def test_internshala_merged_into_lenient_filtered_output() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    rows = parse_internshala_listing_html(html)
    policy = FilterPolicy(mode="lenient")
    accepted = [row for row in rows if policy.evaluate(row).accepted]
    assert accepted, "lenient policy should accept some internshala fixture rows"


@patch.object(InternshalaScraper, "scrape_search_page")
def test_discover_calls_internshala_source(mock_scrape: MagicMock) -> None:
    from src.models import Internship

    mock_scrape.return_value = [
        Internship(
            title="Python Development",
            company="Maxgen Technologies",
            location="Mumbai",
            description=(
                "Python Development intern machine learning Django REST API India "
                "₹ 23,000 - 30,000 /month 6 Months"
            ),
            stipend_inr=30_000,
            duration_months=6,
            apply_url="https://internshala.com/internship/detail/example",
            source="internshala",
        )
    ]
    scraper = InternshipScraper(filter_mode="lenient")
    with patch.object(InternshipScraper, "_discover_manual_urls", return_value=[]):
        with patch.object(InternshipScraper, "_discover_source") as mock_discover:
            def call(name: str, fetch: object) -> list:
                if name == "internshala":
                    return fetch()
                return []

            mock_discover.side_effect = call
            found = scraper.discover(limit=5)
    assert mock_scrape.called
    assert any(item.source == "internshala" for item in found)
