from __future__ import annotations

from pathlib import Path

from .models import (
    ApplicationStrategy,
    InterviewPrep,
    LearningRoadmap,
    RankedInternship,
    SkillGapPlan,
)


class ReportGenerator:
    def __init__(self, reports_dir: str | Path = "reports") -> None:
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_all(
        self,
        ranked: list[RankedInternship],
        skill_gaps: list[SkillGapPlan],
        roadmaps: list[LearningRoadmap],
        prep: list[InterviewPrep],
        strategies: list[ApplicationStrategy],
    ) -> dict[str, Path]:
        outputs = {
            "top_internships": self.reports_dir / "top_internships.md",
            "skill_gap_analysis": self.reports_dir / "skill_gap_analysis.md",
            "learning_roadmaps": self.reports_dir / "learning_roadmaps.md",
            "interview_prep": self.reports_dir / "interview_prep.md",
            "application_strategy": self.reports_dir / "application_strategy.md",
        }
        outputs["top_internships"].write_text(self._top_internships(ranked), encoding="utf-8")
        outputs["skill_gap_analysis"].write_text(self._skill_gaps(skill_gaps), encoding="utf-8")
        outputs["learning_roadmaps"].write_text(self._roadmaps(roadmaps), encoding="utf-8")
        outputs["interview_prep"].write_text(self._prep(prep), encoding="utf-8")
        outputs["application_strategy"].write_text(self._strategies(strategies), encoding="utf-8")
        return outputs

    @staticmethod
    def _top_internships(ranked: list[RankedInternship]) -> str:
        lines = ["# Top Internships", ""]
        for index, item in enumerate(ranked, start=1):
            internship = item.internship
            lines.extend(
                [
                    f"## {index}. {internship.title} - {internship.company}",
                    f"- Location: {internship.location or 'Unknown'}",
                    f"- Stipend: INR {internship.stipend_inr:,}/month",
                    f"- Duration: {internship.duration_months} months",
                    f"- Rank score: {item.rank_score}",
                    f"- Resume fit: {item.match.fit_score}",
                    f"- PPO score: {item.ppo.score}",
                    f"- Company quality: {item.company_research.quality_score}",
                    f"- Apply: {internship.apply_url or 'Not available'}",
                    "",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _skill_gaps(gaps: list[SkillGapPlan]) -> str:
        lines = ["# Skill Gap Analysis", ""]
        for gap in gaps:
            lines.extend([f"## {gap.internship_title} - {gap.company}", ""])
            _section(lines, "Missing", gap.exact_missing_skills)
            _section(lines, "Technologies/tools to learn", gap.technologies_to_learn)
            _section(lines, "Concepts to learn", gap.concepts_to_learn)
            _section(lines, "Suggested projects", gap.project_recommendations)
        return "\n".join(lines)

    @staticmethod
    def _roadmaps(roadmaps: list[LearningRoadmap]) -> str:
        lines = ["# Learning Roadmaps", ""]
        for roadmap in roadmaps:
            lines.extend([f"## {roadmap.internship_title} - {roadmap.company}", ""])
            _section(lines, "1-week roadmap", roadmap.one_week)
            _section(lines, "2-week roadmap", roadmap.two_week)
            _section(lines, "1-month roadmap", roadmap.one_month)
            _section(lines, "Interview readiness checklist", roadmap.interview_readiness_checklist)
        return "\n".join(lines)

    @staticmethod
    def _prep(prep: list[InterviewPrep]) -> str:
        lines = ["# Interview Prep", ""]
        for item in prep:
            lines.extend([f"## {item.internship_title} - {item.company}", ""])
            _section(lines, "Technical questions", item.technical_questions)
            _section(lines, "Behavioral questions", item.behavioral_questions)
            _section(lines, "Project-based questions", item.project_based_questions)
        return "\n".join(lines)

    @staticmethod
    def _strategies(strategies: list[ApplicationStrategy]) -> str:
        lines = ["# Application Strategy", ""]
        for item in strategies:
            lines.extend(
                [
                    f"## {item.internship_title} - {item.company}",
                    f"- Apply now: {'Yes' if item.apply_now else 'After upskilling'}",
                    f"- Competitiveness: {item.competitiveness_score}",
                    f"- Urgency: {item.urgency_score}",
                ]
            )
            _section(lines, "Rationale", item.rationale)
        return "\n".join(lines)


def _section(lines: list[str], title: str, items: list[str]) -> None:
    lines.append(f"### {title}")
    if not items:
        lines.append("- None identified")
    else:
        lines.extend(f"- {item}" for item in items)
    lines.append("")
