from __future__ import annotations

from .models import InterviewPrep, RankedInternship


class InterviewPrepGenerator:
    def generate(self, candidate: RankedInternship) -> InterviewPrep:
        skills = candidate.jd.all_skills[:6] or ["Python", "problem solving", "project design"]
        responsibilities = candidate.jd.responsibilities[:3]
        return InterviewPrep(
            internship_title=candidate.internship.title,
            company=candidate.internship.company,
            technical_questions=[
                f"How have you used {skill} in a real project?" for skill in skills
            ]
            + [
                "Explain the tradeoffs in your latest backend or ML project.",
                "How would you debug a slow API or model inference pipeline?",
            ],
            behavioral_questions=[
                "Tell me about a time you learned a new tool quickly.",
                "How do you handle ambiguous requirements from a mentor or manager?",
                "Why are you interested in this company and this internship?",
                "Describe a project failure and what changed in your process afterward.",
            ],
            project_based_questions=[
                f"How would you approach this responsibility: {item}?" for item in responsibilities
            ]
            + [
                "Walk through your strongest project from requirements to deployment.",
                "What would you improve if you had two more weeks on your project?",
            ],
        )
