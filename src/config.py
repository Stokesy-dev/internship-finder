from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .filter_policy import FilterMode


@dataclass(frozen=True, slots=True)
class AgentSettings:
    resume_path: Path
    jobs_csv: Path | None = None
    internship_urls: tuple[str, ...] = ()
    role_query: str = ""
    min_stipend_inr: int = 20_000
    min_duration_months: int = 6
    filter_mode: FilterMode = "strict"
    rich_reports: bool = False
    ppo_required: bool = False
    live_only: bool = False
    allow_sample_fallback: bool = False
    raw_cache_path: Path = Path("data/internships.json")
    reports_dir: Path = Path("reports")
    limit: int = 30
    top_k: int = 10
    ollama_fast_model: str = "qwen2.5:3b"
    ollama_large_model: str = "qwen2.5:7b"
    ollama_url: str = "http://localhost:11434"
    use_llm: bool = True
    use_embeddings: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
