from __future__ import annotations

import pytest

from src.filter_policy import FilterPolicy
from src.models import Internship


def _listing(
    *,
    stipend_inr: int = 0,
    duration_months: int = 0,
    title: str = "Machine Learning Intern",
    location: str = "Remote India",
) -> Internship:
    return Internship(
        title=title,
        company="Test Co",
        location=location,
        description=(
            "6 month machine learning internship in India. Python, TensorFlow, "
            "scikit-learn. Remote friendly. INR 30000 monthly stipend optional."
        ),
        stipend_inr=stipend_inr,
        duration_months=duration_months,
        apply_url="https://example.com/ml-intern",
        source="test",
        remote=True,
    )


@pytest.mark.parametrize(
    ("mode", "stipend", "duration", "accepted", "reason_fragment"),
    [
        ("lenient", 0, 0, True, "passes all filters"),
        ("lenient", 15_000, 6, False, "stipend 15000"),
        ("lenient", 25_000, 0, True, "unknown: duration"),
        ("strict", 0, 6, False, "stipend unknown"),
        ("strict", 25_000, 3, False, "duration 3"),
        ("strict", 25_000, 6, True, "passes all filters"),
    ],
)
def test_filter_policy_stipend_duration_matrix(
    mode: str,
    stipend: int,
    duration: int,
    accepted: bool,
    reason_fragment: str,
) -> None:
    policy = FilterPolicy(mode=mode)  # type: ignore[arg-type]
    decision = policy.evaluate(_listing(stipend_inr=stipend, duration_months=duration))
    assert decision.accepted is accepted
    assert reason_fragment in decision.reason
    if accepted and stipend == 0 and mode == "lenient":
        assert decision.penalties.get("stipend_unknown") is True


def test_lenient_allows_unknown_when_role_and_geo_match() -> None:
    policy = FilterPolicy(mode="lenient")
    decision = policy.evaluate(_listing(stipend_inr=0, duration_months=0))
    assert decision.accepted
    assert decision.penalties["stipend_unknown"]
    assert decision.penalties["duration_unknown"]


def test_ppo_not_required_by_default() -> None:
    policy = FilterPolicy(mode="strict")
    listing = _listing(stipend_inr=25_000, duration_months=6)
    listing.description = "Backend engineering intern in Bengaluru. Python, FastAPI. No PPO mentioned."
    assert policy.evaluate(listing).accepted


def test_ppo_required_rejects_without_signal() -> None:
    policy = FilterPolicy(mode="strict", ppo_required=True)
    listing = _listing(stipend_inr=25_000, duration_months=6)
    listing.description = "Software engineering intern in India. Python, Docker."
    decision = policy.evaluate(listing)
    assert not decision.accepted
    assert "PPO" in decision.reason
