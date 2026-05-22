from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.coaching_generator import CoachingGenerator
from src.config import AgentSettings
from src.models import (
    CompanyResearch,
    Internship,
    JDProfile,
    MatchResult,
    PPOPrediction,
    RankedInternship,
    SkillGapPlan,
)
from src.ollama_client import OllamaClient
from src.pipeline import InternshipIntelligenceAgent
from src.report_generator import ReportGenerator
from src.skill_gap_analyzer import SkillGapAnalyzer


def _candidate() -> RankedInternship:
    return RankedInternship(
        internship=Internship(
            title="Machine Learning Intern",
            company="Fixture Labs",
            location="Remote India",
            description="machine learning intern Python TensorFlow remote India 6 months",
            stipend_inr=25_000,
            duration_months=6,
            apply_url="https://example.com/ml",
            source="test",
        ),
        jd=JDProfile(
            role_title="Machine Learning Intern",
            required_skills=["Python", "TensorFlow"],
            responsibilities=["Build ML pipelines", "Evaluate models"],
        ),
        match=MatchResult(
            fit_score=72.0,
            confidence_score=0.8,
            matching_skills=["Python"],
            missing_skills=["TensorFlow"],
            semantic_similarity=0.7,
        ),
        ppo=PPOPrediction(score=55.0),
        company_research=CompanyResearch(company="Fixture Labs", quality_score=60.0),
        rank_score=65.0,
    )


def _gap(candidate: RankedInternship) -> SkillGapPlan:
    return SkillGapAnalyzer().analyze(candidate)


def test_template_mode_uses_template_phrasing() -> None:
    coaching = CoachingGenerator(rich_reports=False, use_llm=True)
    gap = _gap(_candidate())
    roadmap = coaching.generate_roadmap(gap, _candidate())
    assert any("Learn fundamentals" in item for item in roadmap.one_week)


@patch.object(OllamaClient, "generate_json")
def test_rich_mode_uses_llm_content(mock_json: MagicMock) -> None:
    mock_json.side_effect = [
        {
            "one_week": ["RICH: Study TensorFlow Keras APIs with a weekly milestone project."],
            "two_week": ["RICH: Deploy a model serving endpoint on Docker."],
            "one_month": ["RICH: Ship portfolio project aligned to JD responsibilities."],
            "interview_readiness_checklist": ["RICH: Complete 20 ML system design flashcards."],
        },
        {
            "technical_questions": ["RICH: Explain bias-variance tradeoff for this team's models."],
            "behavioral_questions": ["RICH: Describe learning TensorFlow under deadline pressure."],
            "project_based_questions": ["RICH: How would you productionize the pipeline described in the JD?"],
        },
        {
            "apply_now": True,
            "competitiveness_score": "High",
            "urgency_score": "Medium",
            "rationale": ["RICH: Strong Python overlap; close TensorFlow gap in two weeks."],
        },
    ]
    llm = OllamaClient(model="qwen2.5:7b")
    coaching = CoachingGenerator(llm=llm, use_llm=True, rich_reports=True)
    candidate = _candidate()
    gap = _gap(candidate)

    roadmap = coaching.generate_roadmap(gap, candidate)
    prep = coaching.generate_prep(candidate)
    strategy = coaching.generate_strategy(candidate)

    assert mock_json.call_count == 3
    assert roadmap.one_week[0].startswith("RICH:")
    assert prep.technical_questions[0].startswith("RICH:")
    assert strategy.rationale[0].startswith("RICH:")


@patch.object(OllamaClient, "generate_json", side_effect=RuntimeError("ollama down"))
def test_rich_mode_falls_back_to_template_on_failure(mock_json: MagicMock) -> None:
    coaching = CoachingGenerator(
        llm=OllamaClient(model="qwen2.5:7b"),
        use_llm=True,
        rich_reports=True,
    )
    gap = _gap(_candidate())
    roadmap = coaching.generate_roadmap(gap, _candidate())
    assert any("Learn fundamentals" in item for item in roadmap.one_week)
    mock_json.assert_called()


@patch.object(OllamaClient, "generate_json")
def test_discover_profile_uses_templates(mock_json: MagicMock, tmp_path: Path) -> None:
    settings = AgentSettings(
        resume_path=Path(__file__).parent / "fixtures" / "resume.pdf",
        jobs_csv=Path(__file__).parent / "fixtures" / "internships.csv",
        filter_mode="lenient",
        rich_reports=False,
        reports_dir=tmp_path / "reports",
        top_k=2,
        use_llm=True,
        use_embeddings=False,
    )
    agent = InternshipIntelligenceAgent(settings)
    gap = SkillGapPlan(
        internship_title="ML Intern",
        company="Co",
        exact_missing_skills=["TensorFlow"],
        technologies_to_learn=[],
        concepts_to_learn=[],
        project_recommendations=[],
    )
    agent.coaching.generate_roadmap(gap, _candidate())
    mock_json.assert_not_called()


@patch.object(OllamaClient, "generate_json")
def test_rich_reports_write_substantive_markdown(mock_json: MagicMock, tmp_path: Path) -> None:
    mock_json.side_effect = [
        {
            "one_week": ["RICH roadmap week1: build TensorFlow baseline."],
            "two_week": ["RICH roadmap week2: add evaluation harness."],
            "one_month": ["RICH roadmap month: portfolio release."],
            "interview_readiness_checklist": ["RICH checklist: mock interview loop."],
        },
        {
            "technical_questions": ["RICH tech Q1"],
            "behavioral_questions": ["RICH behavioral Q1"],
            "project_based_questions": ["RICH project Q1"],
        },
        {
            "apply_now": True,
            "competitiveness_score": "High",
            "urgency_score": "High",
            "rationale": ["RICH strategy: apply this week while fit is strong."],
        },
    ]
    candidate = _candidate()
    gap = _gap(candidate)
    coaching = CoachingGenerator(
        llm=OllamaClient(model="qwen2.5:7b"),
        use_llm=True,
        rich_reports=True,
    )
    roadmaps = [coaching.generate_roadmap(gap, candidate)]
    prep = [coaching.generate_prep(candidate)]
    strategies = [coaching.generate_strategy(candidate)]

    paths = ReportGenerator(tmp_path / "reports").write_all(
        ranked=[candidate],
        skill_gaps=[gap],
        roadmaps=roadmaps,
        prep=prep,
        strategies=strategies,
    )
    roadmaps_md = paths["learning_roadmaps"].read_text(encoding="utf-8")
    prep_md = paths["interview_prep"].read_text(encoding="utf-8")
    strategy_md = paths["application_strategy"].read_text(encoding="utf-8")

    assert "RICH roadmap week1" in roadmaps_md
    assert "RICH tech Q1" in prep_md
    assert "RICH strategy" in strategy_md
    assert len(roadmaps_md) > 200
    assert len(prep_md) > 150
    assert len(strategy_md) > 150


def test_skill_gaps_stay_rule_based_with_rich_coaching() -> None:
    candidate = _candidate()
    gap = SkillGapAnalyzer().analyze(candidate)
    assert gap.exact_missing_skills == candidate.match.missing_skills
