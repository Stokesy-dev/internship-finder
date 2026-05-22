from __future__ import annotations

import argparse

import pytest

from src.main import build_parser, settings_from_args
from src.run_profile import profile_defaults, resolve_filter_mode, resolve_rich_reports


def _parse(argv: list[str]) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def test_discover_defaults() -> None:
    profile = profile_defaults("discover")
    assert profile.filter_mode == "lenient"
    assert profile.rich_reports is False
    assert profile.limit == 30
    assert profile.top_k == 10


def test_shortlist_defaults() -> None:
    profile = profile_defaults("shortlist")
    assert profile.filter_mode == "strict"
    assert profile.rich_reports is True
    assert profile.top_k == 5


def test_settings_from_discover_command() -> None:
    args = _parse(
        [
            "discover",
            "--resume",
            "tests/fixtures/resume.pdf",
            "--no-llm",
            "--no-embeddings",
        ]
    )
    settings = settings_from_args(args)
    assert settings.filter_mode == "lenient"
    assert settings.rich_reports is False
    assert settings.limit == 30
    assert settings.top_k == 10


def test_settings_from_shortlist_command() -> None:
    args = _parse(
        [
            "shortlist",
            "--resume",
            "tests/fixtures/resume.pdf",
            "--no-llm",
            "--no-embeddings",
        ]
    )
    settings = settings_from_args(args)
    assert settings.filter_mode == "strict"
    assert settings.rich_reports is True
    assert settings.top_k == 5


def test_lenient_flag_overrides_shortlist_preset() -> None:
    args = _parse(
        [
            "shortlist",
            "--resume",
            "tests/fixtures/resume.pdf",
            "--lenient",
        ]
    )
    assert settings_from_args(args).filter_mode == "lenient"


def test_no_lenient_overrides_discover_preset() -> None:
    args = _parse(
        [
            "discover",
            "--resume",
            "tests/fixtures/resume.pdf",
            "--no-lenient",
        ]
    )
    assert settings_from_args(args).filter_mode == "strict"


def test_top_k_override() -> None:
    args = _parse(
        [
            "discover",
            "--resume",
            "tests/fixtures/resume.pdf",
            "--top-k",
            "3",
        ]
    )
    assert settings_from_args(args).top_k == 3


def test_cli_help_lists_subcommands() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    help_text = parser.format_help()
    assert "discover" in help_text
    assert "shortlist" in help_text
