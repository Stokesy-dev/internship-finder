from __future__ import annotations

from .models import CompanyResearch, Internship, PPOPrediction


class PPOPredictor:
    def predict(self, internship: Internship, company: CompanyResearch | None = None) -> PPOPrediction:
        text = f"{internship.title} {internship.description}".lower()
        score = 35.0
        signals: list[str] = []
        risks: list[str] = []

        if internship.duration_months >= 6:
            score += 18
            signals.append("Duration is at least 6 months, which improves conversion signal.")
        if any(term in text for term in ["ppo", "pre-placement", "full-time", "full time", "conversion"]):
            score += 25
            signals.append("Description mentions PPO, pre-placement, full-time, or conversion.")
        if any(term in text for term in ["hiring", "expanding", "growth", "scale", "funded"]):
            score += 8
            signals.append("Description contains company growth or hiring language.")
        if company:
            score += min(12, company.quality_score * 0.12)
            signals.extend(company.growth_indicators[:3])
            signals.extend(company.hiring_signals[:2])
        if internship.duration_months < 6:
            score -= 20
            risks.append("Duration below 6 months usually reduces PPO likelihood.")
        if not any(term in text for term in ["ppo", "conversion", "full-time", "full time"]):
            risks.append("No explicit PPO or full-time conversion promise found.")

        return PPOPrediction(score=round(max(0, min(score, 100)), 2), signals=signals, risks=risks)
