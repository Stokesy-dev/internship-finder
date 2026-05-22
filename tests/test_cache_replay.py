from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.internship_scraper import InternshipScraper
from src.models import Internship


def _cached_listing() -> Internship:
    return Internship(
        title="Machine Learning Intern",
        company="Cached Co",
        location="Remote India",
        description="machine learning intern Python TensorFlow scikit-learn remote India",
        stipend_inr=0,
        duration_months=0,
        apply_url="https://example.com/cached-ml",
        source="cache_fixture",
        remote=True,
    )


def _seed_cache(path: Path, listings: list[Internship]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    from dataclasses import asdict

    path.write_text(
        json.dumps([asdict(item) for item in listings], indent=2),
        encoding="utf-8",
    )


@patch.object(InternshipScraper, "_discover_manual_urls", return_value=[])
@patch.object(InternshipScraper, "_discover_source", return_value=[])
def test_empty_live_replays_lenient_cache(
    _manual: object,
    _source: object,
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "internships.json"
    _seed_cache(cache_path, [_cached_listing()])

    scraper = InternshipScraper(
        filter_mode="lenient",
        raw_output_path=cache_path,
        live_only=False,
    )
    found = scraper.discover(limit=10)
    assert len(found) == 1
    assert found[0].company == "Cached Co"


@patch.object(InternshipScraper, "_discover_manual_urls", return_value=[])
@patch.object(InternshipScraper, "_discover_source", return_value=[])
def test_live_only_skips_cache_replay(
    _manual: object,
    _source: object,
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "internships.json"
    _seed_cache(cache_path, [_cached_listing()])

    scraper = InternshipScraper(
        filter_mode="lenient",
        raw_output_path=cache_path,
        live_only=True,
    )
    assert scraper.discover(limit=10) == []


@patch.object(InternshipScraper, "_discover_manual_urls", return_value=[])
@patch.object(InternshipScraper, "_discover_source", return_value=[])
def test_sample_fallback_requires_dev_flag(
    _manual: object,
    _source: object,
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "internships.json"
    scraper = InternshipScraper(
        filter_mode="strict",
        raw_output_path=cache_path,
        allow_sample_fallback=False,
    )
    assert scraper.discover(limit=10) == []

    scraper_dev = InternshipScraper(
        filter_mode="strict",
        raw_output_path=cache_path,
        allow_sample_fallback=True,
    )
    found = scraper_dev.discover(limit=10)
    assert found
    assert all(item.source == "sample_fallback" for item in found)


@patch.object(InternshipScraper, "_discover_manual_urls", return_value=[])
@patch.object(InternshipScraper, "_discover_source", return_value=[])
def test_non_empty_live_saves_raw_then_replays_when_strict_filters_all(
    _manual: object,
    _source: object,
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "internships.json"
    live_listing = _cached_listing()
    live_listing.source = "greenhouse"

    with patch.object(InternshipScraper, "_discover_source", return_value=[live_listing]):
        scraper = InternshipScraper(
            filter_mode="strict",
            raw_output_path=cache_path,
        )
        scraper._discover_manual_urls = lambda urls, limit: []  # type: ignore[method-assign]
        # strict rejects zero stipend from live; replay same cache with lenient
        assert scraper.discover(limit=5) == []

    assert cache_path.exists()
    saved = json.loads(cache_path.read_text(encoding="utf-8"))
    assert len(saved) == 1

    scraper_lenient = InternshipScraper(
        filter_mode="lenient",
        raw_output_path=cache_path,
    )
    with patch.object(InternshipScraper, "_discover_manual_urls", return_value=[]):
        with patch.object(InternshipScraper, "_discover_source", return_value=[]):
            replayed = scraper_lenient.discover(limit=5)
    assert len(replayed) == 1


def test_save_raw_skips_empty_list(tmp_path: Path) -> None:
    cache_path = tmp_path / "internships.json"
    _seed_cache(cache_path, [_cached_listing()])
    scraper = InternshipScraper(raw_output_path=cache_path)
    scraper._save_raw([])
    assert len(json.loads(cache_path.read_text(encoding="utf-8"))) == 1
