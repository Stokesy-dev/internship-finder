from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .coaching_generator import CoachingGenerator
from .company_research import CompanyResearcher
from .config import AgentSettings
from .jd_parser import JDParser
from .job_loader import InternshipRepository
from .models import (
    ApplicationStrategy,
    Internship,
    InterviewPrep,
    LearningRoadmap,
    RankedInternship,
    ResumeProfile,
    SkillGapPlan,
)
from .ollama_router import OllamaRouter
from .ppo_predictor import PPOPredictor
from .ranking_engine import RankingEngine
from .report_generator import ReportGenerator
from .resume_matcher import ResumeMatcher
from .resume_parser import ResumeParser
from .skill_gap_analyzer import SkillGapAnalyzer


@dataclass(slots=True)
class AgentResult:
    ranked: list[RankedInternship]
    skill_gaps: list[SkillGapPlan]
    roadmaps: list[LearningRoadmap]
    interview_prep: list[InterviewPrep]
    application_strategies: list[ApplicationStrategy]
    report_paths: dict[str, Path]


class InternshipIntelligenceAgent:
    def __init__(self, settings: AgentSettings) -> None:
        self.settings = settings
        self.ollama = OllamaRouter.from_settings(
            fast_model=settings.ollama_fast_model,
            large_model=settings.ollama_large_model,
            base_url=settings.ollama_url,
        )
        self.resume_parser = ResumeParser()
        self.internships = InternshipRepository(
            min_stipend_inr=settings.min_stipend_inr,
            min_duration_months=settings.min_duration_months,
            role_query=settings.role_query,
            filter_mode=settings.filter_mode,
            ppo_required=settings.ppo_required,
            live_only=settings.live_only,
            allow_sample_fallback=settings.allow_sample_fallback,
            raw_output_path=settings.raw_cache_path,
        )
        self.jd_parser = JDParser(llm=self.ollama.fast, use_llm=settings.use_llm)
        self.company_researcher = CompanyResearcher(llm=self.ollama.large, use_llm=settings.use_llm)
        self.matcher = ResumeMatcher(
            model_name=settings.embedding_model,
            use_sentence_transformers=settings.use_embeddings,
        )
        self.ppo_predictor = PPOPredictor()
        self.ranking_engine = RankingEngine(filter_mode=settings.filter_mode)
        self.gap_analyzer = SkillGapAnalyzer()
        self.coaching = CoachingGenerator(
            llm=self.ollama.large,
            use_llm=settings.use_llm,
            rich_reports=settings.rich_reports,
        )
        self.report_generator = ReportGenerator(settings.reports_dir)

    def run(self) -> AgentResult:
        resume = self.resume_parser.parse_pdf(self.settings.resume_path)
        internships = self.internships.load(
            limit=self.settings.limit,
            jobs_csv=self.settings.jobs_csv,
            internship_urls=self.settings.internship_urls,
            seed_file=self.settings.seed_file,
        )
        ranked = self.ranking_engine.rank(
            [self._score_internship(internship, resume) for internship in internships]
        )[: self.settings.top_k]

        skill_gaps = [self.gap_analyzer.analyze(candidate) for candidate in ranked]
        roadmaps = [
            self.coaching.generate_roadmap(gap, candidate)
            for gap, candidate in zip(skill_gaps, ranked, strict=True)
        ]
        prep = [self.coaching.generate_prep(candidate) for candidate in ranked]
        strategies = [self.coaching.generate_strategy(candidate) for candidate in ranked]
        report_paths = self.report_generator.write_all(
            ranked=ranked,
            skill_gaps=skill_gaps,
            roadmaps=roadmaps,
            prep=prep,
            strategies=strategies,
        )
        return AgentResult(
            ranked=ranked,
            skill_gaps=skill_gaps,
            roadmaps=roadmaps,
            interview_prep=prep,
            application_strategies=strategies,
            report_paths=report_paths,
        )

    def _score_internship(self, internship: Internship, resume: ResumeProfile) -> RankedInternship:
        jd = self.jd_parser.parse(internship.title, internship.description)
        company = self.company_researcher.research(internship)
        match = self.matcher.match(resume, jd)
        ppo = self.ppo_predictor.predict(internship, company)
        return RankedInternship(
            internship=internship,
            jd=jd,
            match=match,
            ppo=ppo,
            company_research=company,
            rank_score=0.0,
        )
