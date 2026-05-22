from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Internship:
    title: str
    company: str
    location: str = ""
    description: str = ""
    stipend_inr: int = 0
    duration_months: int = 0
    apply_url: str = ""
    source: str = ""
    remote: bool = False
    posted_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResumeProfile:
    raw_text: str
    skills: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JDProfile:
    role_title: str
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    experience_expectations: list[str] = field(default_factory=list)

    @property
    def all_skills(self) -> list[str]:
        return sorted(set(self.required_skills + self.preferred_skills + self.tools))


@dataclass(slots=True)
class MatchResult:
    fit_score: float
    confidence_score: float
    matching_skills: list[str]
    missing_skills: list[str]
    semantic_similarity: float


@dataclass(slots=True)
class CompanyResearch:
    company: str
    overview: str = ""
    products: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    growth_indicators: list[str] = field(default_factory=list)
    hiring_signals: list[str] = field(default_factory=list)
    quality_score: float = 0.0


@dataclass(slots=True)
class PPOPrediction:
    score: float
    signals: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RankedInternship:
    internship: Internship
    jd: JDProfile
    match: MatchResult
    ppo: PPOPrediction
    company_research: CompanyResearch
    rank_score: float


@dataclass(slots=True)
class SkillGapPlan:
    internship_title: str
    company: str
    exact_missing_skills: list[str]
    technologies_to_learn: list[str]
    concepts_to_learn: list[str]
    project_recommendations: list[str]


@dataclass(slots=True)
class LearningRoadmap:
    internship_title: str
    company: str
    one_week: list[str]
    two_week: list[str]
    one_month: list[str]
    interview_readiness_checklist: list[str]


@dataclass(slots=True)
class InterviewPrep:
    internship_title: str
    company: str
    technical_questions: list[str]
    behavioral_questions: list[str]
    project_based_questions: list[str]


@dataclass(slots=True)
class ApplicationStrategy:
    internship_title: str
    company: str
    apply_now: bool
    competitiveness_score: str
    urgency_score: str
    rationale: list[str]
