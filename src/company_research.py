from __future__ import annotations

from .models import CompanyResearch, Internship
from .ollama_client import OllamaClient


class CompanyResearcher:
    def __init__(self, llm: OllamaClient | None = None, use_llm: bool = True) -> None:
        self.llm = llm or OllamaClient()
        self.use_llm = use_llm

    def research(self, internship: Internship) -> CompanyResearch:
        fallback = self._heuristic_research(internship)
        if not self.use_llm:
            return fallback
        data = self.llm.generate_json(
            prompt=(
                "Research this company only from the provided internship context. "
                "Do not invent funding or metrics.\n"
                f"Company: {internship.company}\n"
                f"Role: {internship.title}\n"
                f"Description: {internship.description[:5000]}\n"
                "Schema: {\"overview\":\"\",\"products\":[],\"competitors\":[],"
                "\"growth_indicators\":[],\"hiring_signals\":[],\"quality_score\":0}"
            ),
            fallback={},
            system="You are conservative. Use 'unknown' when evidence is absent.",
        )
        if not data:
            return fallback
        return CompanyResearch(
            company=internship.company,
            overview=str(data.get("overview") or fallback.overview),
            products=_as_list(data.get("products")),
            competitors=_as_list(data.get("competitors")),
            growth_indicators=_as_list(data.get("growth_indicators")) or fallback.growth_indicators,
            hiring_signals=_as_list(data.get("hiring_signals")) or fallback.hiring_signals,
            quality_score=float(data.get("quality_score") or fallback.quality_score),
        )

    @staticmethod
    def _heuristic_research(internship: Internship) -> CompanyResearch:
        text = internship.description.lower()
        growth = [
            signal
            for term, signal in {
                "funded": "Funding mentioned in internship description.",
                "scale": "Scaling language appears in internship description.",
                "growth": "Growth language appears in internship description.",
                "hiring": "Hiring signal appears in internship description.",
                "startup": "Startup environment mentioned.",
            }.items()
            if term in text
        ]
        hiring = ["Internship listing is active on a public job source."] if internship.apply_url else []
        quality = 50 + min(20, len(growth) * 5) + (10 if internship.apply_url else 0)
        return CompanyResearch(
            company=internship.company,
            overview=f"{internship.company} context extracted from the internship description.",
            growth_indicators=growth,
            hiring_signals=hiring,
            quality_score=float(min(100, quality)),
        )


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
