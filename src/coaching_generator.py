from __future__ import annotations

import logging
from typing import Any

from .application_strategy import ApplicationStrategyGenerator
from .interview_prep import InterviewPrepGenerator
from .learning_roadmap import LearningRoadmapGenerator
from .models import (
    ApplicationStrategy,
    InterviewPrep,
    LearningRoadmap,
    RankedInternship,
    SkillGapPlan,
)
from .ollama_client import OllamaClient

LOGGER = logging.getLogger(__name__)


class CoachingGenerator:
    """Template coaching by default; large-model LLM coaching when rich mode is on."""

    def __init__(
        self,
        llm: OllamaClient | None = None,
        *,
        use_llm: bool = True,
        rich_reports: bool = False,
    ) -> None:
        self.llm = llm
        self.use_llm = use_llm
        self.rich_reports = rich_reports
        self._roadmap_template = LearningRoadmapGenerator()
        self._prep_template = InterviewPrepGenerator()
        self._strategy_template = ApplicationStrategyGenerator()

    def generate_roadmap(
        self,
        gap: SkillGapPlan,
        candidate: RankedInternship,
    ) -> LearningRoadmap:
        template = self._roadmap_template.generate(gap)
        if not self._use_rich():
            return template
        rich = self._rich_roadmap(gap, candidate, template)
        return rich if rich is not None else template

    def generate_prep(self, candidate: RankedInternship) -> InterviewPrep:
        template = self._prep_template.generate(candidate)
        if not self._use_rich():
            return template
        rich = self._rich_prep(candidate)
        return rich if rich is not None else template

    def generate_strategy(self, candidate: RankedInternship) -> ApplicationStrategy:
        template = self._strategy_template.generate(candidate)
        if not self._use_rich():
            return template
        rich = self._rich_strategy(candidate, template)
        return rich if rich is not None else template

    def _use_rich(self) -> bool:
        return self.use_llm and self.rich_reports and self.llm is not None

    def _rich_roadmap(
        self,
        gap: SkillGapPlan,
        candidate: RankedInternship,
        template: LearningRoadmap,
    ) -> LearningRoadmap | None:
        data = self._llm_json(
            prompt=(
                "Create a practical learning roadmap for this internship application.\n"
                f"Role: {gap.internship_title} at {gap.company}\n"
                f"Missing skills: {', '.join(gap.exact_missing_skills) or 'none listed'}\n"
                f"Technologies to learn: {', '.join(gap.technologies_to_learn)}\n"
                f"Concepts: {', '.join(gap.concepts_to_learn)}\n"
                f"Suggested projects: {', '.join(gap.project_recommendations)}\n"
                f"Resume fit score: {candidate.match.fit_score}\n"
                f"JD skills: {', '.join(candidate.jd.all_skills[:12])}\n"
                "Return 4-6 specific actionable bullets per timeframe.\n"
                'Schema: {"one_week":[],"two_week":[],"one_month":[],'
                '"interview_readiness_checklist":[]}'
            ),
            context="roadmap",
        )
        if not data:
            return None
        one_week = _as_list(data.get("one_week"))
        two_week = _as_list(data.get("two_week"))
        one_month = _as_list(data.get("one_month"))
        checklist = _as_list(data.get("interview_readiness_checklist"))
        if not any([one_week, two_week, one_month, checklist]):
            return None
        return LearningRoadmap(
            internship_title=gap.internship_title,
            company=gap.company,
            one_week=one_week or template.one_week,
            two_week=two_week or template.two_week,
            one_month=one_month or template.one_month,
            interview_readiness_checklist=checklist or template.interview_readiness_checklist,
        )

    def _rich_prep(self, candidate: RankedInternship) -> InterviewPrep | None:
        data = self._llm_json(
            prompt=(
                "Create interview preparation questions tailored to this internship.\n"
                f"Role: {candidate.internship.title} at {candidate.internship.company}\n"
                f"Required skills: {', '.join(candidate.jd.required_skills)}\n"
                f"Responsibilities: {', '.join(candidate.jd.responsibilities[:6])}\n"
                f"Description excerpt: {candidate.internship.description[:2500]}\n"
                "Provide realistic, role-specific questions (5-8 per category).\n"
                'Schema: {"technical_questions":[],"behavioral_questions":[],'
                '"project_based_questions":[]}'
            ),
            context="interview prep",
        )
        if not data:
            return None
        technical = _as_list(data.get("technical_questions"))
        behavioral = _as_list(data.get("behavioral_questions"))
        project_based = _as_list(data.get("project_based_questions"))
        if not (technical or behavioral or project_based):
            return None
        return InterviewPrep(
            internship_title=candidate.internship.title,
            company=candidate.internship.company,
            technical_questions=technical,
            behavioral_questions=behavioral,
            project_based_questions=project_based,
        )

    def _rich_strategy(
        self,
        candidate: RankedInternship,
        template: ApplicationStrategy,
    ) -> ApplicationStrategy | None:
        data = self._llm_json(
            prompt=(
                "Recommend an application strategy for this internship.\n"
                f"Role: {candidate.internship.title} at {candidate.internship.company}\n"
                f"Resume fit: {candidate.match.fit_score}\n"
                f"Rank score: {candidate.rank_score}\n"
                f"PPO score: {candidate.ppo.score}\n"
                f"Missing skills: {', '.join(candidate.match.missing_skills[:8])}\n"
                f"Template suggestion apply_now={template.apply_now}, "
                f"competitiveness={template.competitiveness_score}, urgency={template.urgency_score}\n"
                "Ground recommendations in the evidence above.\n"
                'Schema: {"apply_now":true,"competitiveness_score":"High|Medium|Low",'
                '"urgency_score":"High|Medium|Low","rationale":[]}'
            ),
            context="application strategy",
        )
        if not data:
            return None
        rationale = _as_list(data.get("rationale"))
        if not rationale:
            return None
        return ApplicationStrategy(
            internship_title=candidate.internship.title,
            company=candidate.internship.company,
            apply_now=bool(data.get("apply_now", template.apply_now)),
            competitiveness_score=str(
                data.get("competitiveness_score") or template.competitiveness_score
            ),
            urgency_score=str(data.get("urgency_score") or template.urgency_score),
            rationale=rationale,
        )

    def _llm_json(self, prompt: str, context: str) -> dict[str, Any]:
        if not self.llm:
            return {}
        try:
            return self.llm.generate_json(
                prompt=prompt,
                fallback={},
                system=(
                    "You are an internship career coach for India tech roles. "
                    "Be specific and actionable. Return only JSON."
                ),
            )
        except Exception as exc:
            LOGGER.warning("Rich %s LLM failed, using template fallback: %s", context, exc)
            return {}

def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
