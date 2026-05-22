from __future__ import annotations

from .models import JDProfile
from .ollama_client import OllamaClient
from .text_utils import clean_text, extract_known_skills, split_bullets, unique_preserve_order


class JDParser:
    def __init__(self, llm: OllamaClient | None = None, use_llm: bool = True) -> None:
        self.llm = llm or OllamaClient()
        self.use_llm = use_llm

    def parse(self, title: str, description: str) -> JDProfile:
        text = clean_text(description)
        fallback = self._heuristic_parse(title, text)
        if not self.use_llm or not text:
            return fallback

        data = self.llm.generate_json(
            prompt=(
                "Extract internship job-description fields.\n"
                f"Title: {title}\nDescription: {text[:6000]}\n"
                "Schema: {\"required_skills\":[],\"preferred_skills\":[],\"tools\":[],"
                "\"responsibilities\":[],\"experience_expectations\":[]}"
            ),
            fallback={},
            system="You are a precise recruiting analyst. Extract only evidence-backed fields.",
        )
        if not data:
            return fallback
        return JDProfile(
            role_title=title,
            required_skills=unique_preserve_order(
                _as_list(data.get("required_skills")) or fallback.required_skills
            ),
            preferred_skills=unique_preserve_order(_as_list(data.get("preferred_skills"))),
            tools=unique_preserve_order(_as_list(data.get("tools")) or fallback.tools),
            responsibilities=unique_preserve_order(
                _as_list(data.get("responsibilities")) or fallback.responsibilities
            ),
            experience_expectations=unique_preserve_order(
                _as_list(data.get("experience_expectations"))
            ),
        )

    @staticmethod
    def _heuristic_parse(title: str, text: str) -> JDProfile:
        skills = extract_known_skills(f"{title} {text}")
        responsibilities = [
            item
            for item in split_bullets(text, max_items=8)
            if any(term in item.lower() for term in ["build", "develop", "work", "design", "deploy", "analyze"])
        ]
        tools = [skill for skill in skills if skill in {"Docker", "AWS", "GCP", "Azure", "Git", "Kubernetes", "ChromaDB"}]
        return JDProfile(
            role_title=title,
            required_skills=skills[:8],
            preferred_skills=skills[8:14],
            tools=tools,
            responsibilities=responsibilities[:6],
            experience_expectations=[
                item
                for item in split_bullets(text, max_items=6)
                if "experience" in item.lower() or "familiar" in item.lower()
            ],
        )


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
