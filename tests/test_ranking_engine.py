from __future__ import annotations

from src.models import (
    CompanyResearch,
    Internship,
    JDProfile,
    MatchResult,
    PPOPrediction,
    RankedInternship,
)
from src.ranking_engine import RankingEngine


def _ranked(stipend_inr: int, fit_score: float = 80.0) -> RankedInternship:
    return RankedInternship(
        internship=Internship(
            title="ML Intern",
            company="Co",
            location="Remote India",
            description="machine learning intern India",
            stipend_inr=stipend_inr,
            duration_months=6,
            apply_url="https://example.com/a",
            source="test",
        ),
        jd=JDProfile(role_title="ML Intern"),
        match=MatchResult(
            fit_score=fit_score,
            confidence_score=0.9,
            matching_skills=["Python"],
            missing_skills=[],
            semantic_similarity=0.8,
        ),
        ppo=PPOPrediction(score=50.0),
        company_research=CompanyResearch(company="Co", quality_score=50.0),
        rank_score=0.0,
    )


def test_zero_stipend_ranks_below_known_stipend_with_equal_fit() -> None:
    engine = RankingEngine(filter_mode="lenient")
    unknown = _ranked(0)
    known = _ranked(30_000)
    ranked = engine.rank([unknown, known])
    assert ranked[0].internship.stipend_inr == 30_000
    assert engine.score(unknown) < engine.score(known)
    assert engine._stipend_score(unknown.internship) == 0.0
    assert engine._stipend_score(known.internship) > 0.0
