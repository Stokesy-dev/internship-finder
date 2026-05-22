from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import AgentSettings
from src.pipeline import AgentResult, InternshipIntelligenceAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Internship Opportunity Intelligence Agent"
    )
    parser.add_argument("--resume", required=True, help="Path to PDF resume.")
    parser.add_argument("--jobs-csv", help="Optional CSV of internship listings to rank.")
    parser.add_argument(
        "--internship-url",
        action="append",
        default=[],
        help="Manual internship or careers URL. Can be passed multiple times.",
    )
    parser.add_argument(
        "--internship-urls-file",
        help="Optional text file with one internship or careers URL per line.",
    )
    parser.add_argument("--limit", type=int, default=30, help="Maximum internships to process.")
    parser.add_argument("--top-k", type=int, default=10, help="Top internships for detailed reports.")
    parser.add_argument("--role", default="", help="Role query to filter internships, for example 'data science intern'.")
    parser.add_argument("--min-stipend", type=int, default=20_000, help="Minimum monthly stipend in INR.")
    parser.add_argument("--min-duration", type=int, default=6, help="Minimum internship duration in months.")
    parser.add_argument("--ppo-required", action="store_true", help="Require PPO or full-time conversion signal.")
    parser.add_argument("--live", action="store_true", help="Enforce live discovery only; disables sample fallback.")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name.")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL.")
    parser.add_argument("--no-llm", action="store_true", help="Disable Ollama extraction and use heuristics only.")
    parser.add_argument("--no-embeddings", action="store_true", help="Disable sentence-transformers and use lexical similarity.")
    parser.add_argument("--reports-dir", default="reports", help="Directory for markdown reports.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def settings_from_args(args: argparse.Namespace) -> AgentSettings:
    internship_urls = _collect_urls(args.internship_url, args.internship_urls_file)
    return AgentSettings(
        resume_path=Path(args.resume),
        jobs_csv=Path(args.jobs_csv) if args.jobs_csv else None,
        internship_urls=tuple(internship_urls),
        role_query=args.role,
        min_stipend_inr=args.min_stipend,
        min_duration_months=args.min_duration,
        ppo_required=args.ppo_required,
        live_only=args.live,
        reports_dir=Path(args.reports_dir),
        limit=args.limit,
        top_k=args.top_k,
        ollama_model=args.model,
        ollama_url=args.ollama_url,
        use_llm=not args.no_llm,
        use_embeddings=not args.no_embeddings,
    )


def _collect_urls(cli_urls: list[str], urls_file: str | None) -> list[str]:
    urls = [url.strip() for url in cli_urls if url.strip()]
    if urls_file:
        path = Path(urls_file)
        file_urls = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        urls.extend(file_urls)
    return list(dict.fromkeys(urls))


def run(args: argparse.Namespace) -> AgentResult:
    return InternshipIntelligenceAgent(settings_from_args(args)).run()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")
    result = run(args)
    for name, path in result.report_paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
