from __future__ import annotations

from .models import ApplicationStrategy, RankedInternship


class ApplicationStrategyGenerator:
    def generate(self, candidate: RankedInternship) -> ApplicationStrategy:
        fit = candidate.match.fit_score
        urgency = self._urgency(candidate)
        apply_now = fit >= 65 or (fit >= 50 and urgency == "High")
        rationale = [
            f"Resume fit score is {fit}.",
            f"PPO score is {candidate.ppo.score}.",
            f"Rank score is {candidate.rank_score}.",
        ]
        if candidate.match.missing_skills:
            rationale.append("Close gaps: " + ", ".join(candidate.match.missing_skills[:5]))
        return ApplicationStrategy(
            internship_title=candidate.internship.title,
            company=candidate.internship.company,
            apply_now=apply_now,
            competitiveness_score=self._competitiveness(fit),
            urgency_score=urgency,
            rationale=rationale,
        )

    @staticmethod
    def _competitiveness(fit: float) -> str:
        if fit >= 75:
            return "High"
        if fit >= 50:
            return "Medium"
        return "Low"

    @staticmethod
    def _urgency(candidate: RankedInternship) -> str:
        text = f"{candidate.internship.posted_at} {candidate.internship.description}".lower()
        if any(term in text for term in ["urgent", "immediate", "actively hiring"]):
            return "High"
        if candidate.internship.apply_url:
            return "Medium"
        return "Low"
