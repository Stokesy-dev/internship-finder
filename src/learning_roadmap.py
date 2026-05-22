from __future__ import annotations

from .models import LearningRoadmap, SkillGapPlan


class LearningRoadmapGenerator:
    def generate(self, gap: SkillGapPlan) -> LearningRoadmap:
        missing = gap.exact_missing_skills or ["role fundamentals"]
        first = missing[:3]
        second = missing[3:6] or first
        return LearningRoadmap(
            internship_title=gap.internship_title,
            company=gap.company,
            one_week=[
                f"Learn fundamentals of {skill} with one small exercise." for skill in first
            ]
            + ["Rewrite resume bullets to highlight matching project evidence."],
            two_week=[
                f"Integrate {skill} into one deployable mini-project." for skill in second
            ]
            + ["Add tests, README, screenshots, and measurable outcomes."],
            one_month=[
                "Complete one end-to-end project mapped to the internship responsibilities.",
                "Deploy the project and prepare a 2-minute technical walkthrough.",
                "Practice 30 role-specific questions and review weak areas.",
            ],
            interview_readiness_checklist=[
                "Can explain every matching and missing skill honestly.",
                "Can walk through one relevant project architecture end to end.",
                "Can solve basic Python, SQL, API, and ML/DS questions for the role.",
                "Has a tailored resume and concise application note ready.",
            ],
        )
