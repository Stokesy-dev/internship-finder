from __future__ import annotations

from .models import RankedInternship, SkillGapPlan


class SkillGapAnalyzer:
    def analyze(self, candidate: RankedInternship) -> SkillGapPlan:
        missing = candidate.match.missing_skills
        technologies = [skill for skill in missing if _is_tool(skill)]
        concepts = [skill for skill in missing if skill not in technologies]
        if not concepts and candidate.jd.responsibilities:
            concepts = ["Role-specific implementation patterns", "System design basics"]
        return SkillGapPlan(
            internship_title=candidate.internship.title,
            company=candidate.internship.company,
            exact_missing_skills=missing,
            technologies_to_learn=technologies,
            concepts_to_learn=concepts,
            project_recommendations=self._projects(missing, candidate.internship.title),
        )

    @staticmethod
    def _projects(missing: list[str], title: str) -> list[str]:
        lowered = " ".join([title, *missing]).lower()
        projects: list[str] = []
        if "fastapi" in lowered or "docker" in lowered:
            projects.append("Deploy a resume matching API using FastAPI and Docker.")
        if "aws" in lowered or "gcp" in lowered or "azure" in lowered:
            projects.append("Ship an ML inference service on a cloud VM with logging and health checks.")
        if "rag" in lowered or "llm" in lowered or "langchain" in lowered:
            projects.append("Build a RAG assistant over internship JDs with vector search and evaluation.")
        if "backend" in lowered or "sql" in lowered:
            projects.append("Build a production-style internship tracker with REST APIs, SQL schema, and tests.")
        if not projects:
            projects.append("Build a focused portfolio project that uses the top 3 missing skills in one deployable app.")
        return projects


def _is_tool(skill: str) -> bool:
    tools = {"Docker", "AWS", "GCP", "Azure", "FastAPI", "Django", "Flask", "Git", "Kubernetes", "ChromaDB", "PostgreSQL", "MongoDB"}
    return skill in tools
