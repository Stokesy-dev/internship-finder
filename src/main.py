from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import AgentSettings
from src.pipeline import AgentResult, InternshipIntelligenceAgent
from src.run_profile import (
    RunProfileName,
    profile_defaults,
    resolve_filter_mode,
    resolve_rich_reports,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Internship Opportunity Intelligence Agent",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="COMMAND",
        help="Run profile: discover (explore) or shortlist (apply-ready)",
    )

    discover = subparsers.add_parser(
        "discover",
        help="Weekly exploration: lenient filters, broader top-k (default 30/10).",
        description=(
            "Discover internships with lenient filtering so listings with unknown "
            "stipend or duration still appear (ranked lower). Use for exploration."
        ),
    )
    shortlist = subparsers.add_parser(
        "shortlist",
        help="Apply-ready run: strict filters, focused top-k (default 30/5).",
        description=(
            "Shortlist internships with strict filtering on known stipend and duration. "
            "Use when you are ready to apply."
        ),
    )

    for sub in (discover, shortlist):
        _add_run_arguments(sub)

    return parser


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
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
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum internships to process (profile default if omitted).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Top internships for detailed reports (profile default if omitted).",
    )
    parser.add_argument(
        "--role",
        default="",
        help="Role query to filter internships, for example 'data science intern'.",
    )
    parser.add_argument(
        "--min-stipend",
        type=int,
        default=None,
        help="Minimum monthly stipend in INR (default 20000).",
    )
    parser.add_argument(
        "--min-duration",
        type=int,
        default=None,
        help="Minimum internship duration in months (default 6).",
    )
    parser.add_argument("--ppo-required", action="store_true", help="Require PPO or full-time conversion signal.")
    parser.add_argument(
        "--lenient",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Lenient filters (allow unknown stipend/duration). Overrides profile default.",
    )
    parser.add_argument(
        "--rich-reports",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Use LLM-rich coaching sections (wired in a future release). Overrides profile default.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Live discovery only; disables cache replay and sample fallback.",
    )
    parser.add_argument(
        "--allow-sample-fallback",
        action="store_true",
        help="Dev only: use fabricated sample internships when live discovery and cache replay fail.",
    )
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name.")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL.")
    parser.add_argument("--no-llm", action="store_true", help="Disable Ollama extraction and use heuristics only.")
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Disable sentence-transformers and use lexical similarity.",
    )
    parser.add_argument("--reports-dir", default="reports", help="Directory for markdown reports.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])


def settings_from_args(args: argparse.Namespace) -> AgentSettings:
    command: RunProfileName = args.command
    profile = profile_defaults(command)
    internship_urls = _collect_urls(args.internship_url, args.internship_urls_file)

    return AgentSettings(
        resume_path=Path(args.resume),
        jobs_csv=Path(args.jobs_csv) if args.jobs_csv else None,
        internship_urls=tuple(internship_urls),
        role_query=args.role,
        min_stipend_inr=args.min_stipend if args.min_stipend is not None else 20_000,
        min_duration_months=args.min_duration if args.min_duration is not None else 6,
        filter_mode=resolve_filter_mode(profile, lenient=args.lenient),
        rich_reports=resolve_rich_reports(profile, rich_reports=args.rich_reports),
        ppo_required=args.ppo_required,
        live_only=args.live,
        allow_sample_fallback=args.allow_sample_fallback,
        raw_cache_path=Path("data/internships.json"),
        reports_dir=Path(args.reports_dir),
        limit=args.limit if args.limit is not None else profile.limit,
        top_k=args.top_k if args.top_k is not None else profile.top_k,
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
