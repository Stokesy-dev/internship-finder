from __future__ import annotations

from .filter_policy import FilterMode
from .models import Internship, RankedInternship


class RankingEngine:
    def __init__(self, filter_mode: FilterMode = "strict") -> None:
        self.filter_mode = filter_mode

    def rank(self, candidates: list[RankedInternship]) -> list[RankedInternship]:
        for candidate in candidates:
            candidate.rank_score = self.score(candidate)
        return sorted(candidates, key=lambda item: item.rank_score, reverse=True)

    def score(self, candidate: RankedInternship) -> float:
        stipend_score = self._stipend_score(candidate.internship)
        total = (
            stipend_score * 0.25
            + candidate.ppo.score * 0.25
            + candidate.match.fit_score * 0.35
            + candidate.company_research.quality_score * 0.15
        )
        return round(total, 2)

    @staticmethod
    def _stipend_score(internship: Internship) -> float:
        if internship.stipend_inr <= 0:
            return 0.0
        return round(min(100.0, internship.stipend_inr / 700), 2)
