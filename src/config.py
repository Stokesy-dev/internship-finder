from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AgentSettings:
    resume_path: Path
    jobs_csv: Path | None = None
    internship_urls: tuple[str, ...] = ()
    role_query: str = ""
    min_stipend_inr: int = 20_000
    min_duration_months: int = 6
    ppo_required: bool = False
    live_only: bool = False
    reports_dir: Path = Path("reports")
    limit: int = 30
    top_k: int = 10
    ollama_model: str = "llama3.1:8b"
    ollama_url: str = "http://localhost:11434"
    use_llm: bool = True
    use_embeddings: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
