from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from .company_careers_scraper import CompanyCareersScraper
from .filter_policy import FilterMode, FilterPolicy
from .greenhouse_scraper import GreenhouseScraper
from .internshala_scraper import InternshalaScraper
from .lever_scraper import LeverScraper
from .models import Internship
from .scraper_http import ScraperHttpClient
from .wellfound_scraper import DEFAULT_SEARCH_QUERIES, WellfoundScraper

LOGGER = logging.getLogger(__name__)


class InternshipScraper:
    def __init__(
        self,
        min_stipend_inr: int = 20_000,
        min_duration_months: int = 6,
        role_query: str = "",
        ppo_required: bool = False,
        live_only: bool = False,
        allow_sample_fallback: bool = False,
        filter_mode: FilterMode = "strict",
        raw_output_path: str | Path = "data/internships.json",
        timeout_seconds: int = 15,
        retries: int = 2,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self.filter_policy = FilterPolicy(
            mode=filter_mode,
            min_stipend_inr=min_stipend_inr,
            min_duration_months=min_duration_months,
            role_query=role_query,
            ppo_required=ppo_required,
        )
        self.live_only = live_only
        self.allow_sample_fallback = allow_sample_fallback
        self.raw_output_path = Path(raw_output_path)
        self.http = ScraperHttpClient(
            timeout_seconds=timeout_seconds,
            retries=retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        self.greenhouse = GreenhouseScraper(self.http)
        self.internshala = InternshalaScraper(self.http)
        self.lever = LeverScraper(self.http)
        self.wellfound = WellfoundScraper(self.http)
        self.company_careers = CompanyCareersScraper(self.http)

    def discover(
        self, limit: int = 50, manual_urls: list[str] | None = None, seed_file: Path | None = None
    ) -> list[Internship]:
        successful_requests_before = self.http.successful_requests
        discovered: list[Internship] = []
        
        greenhouse_seeds, lever_seeds, manual_seeds = self._parse_seed_file(seed_file)
        all_manual_urls = (manual_urls or []) + manual_seeds
        
        manual = self._discover_manual_urls(all_manual_urls, limit)
        discovered.extend(manual)
        discovered.extend(
            self._discover_source("greenhouse", lambda: self.greenhouse.discover(boards=greenhouse_seeds or None, limit=limit))
        )
        discovered.extend(
            self._discover_source("internshala", lambda: self.internshala.discover(limit=limit))
        )
        discovered.extend(
            self._discover_source("lever", lambda: self.lever.discover(companies=lever_seeds or None, limit=limit))
        )
        search_queries = self._search_queries()
        discovered.extend(
            self._discover_source(
                "wellfound",
                lambda: self.wellfound.discover(queries=search_queries, limit=limit),
            )
        )
        discovered.extend(
            self._discover_source(
                "company_careers",
                lambda: self.company_careers.discover(limit=limit),
            )
        )

        raw = self._dedupe(discovered)
        if raw:
            self._save_raw(raw)
        else:
            LOGGER.info("Live discovery returned zero raw listings; preserving existing cache")

        filtered = self.filter_internships(raw) if raw else []
        if filtered:
            LOGGER.info("Discovery complete raw=%s filtered=%s", len(raw), len(filtered))
            return filtered[:limit]

        if self.live_only:
            LOGGER.error(
                "--live enabled: %s raw listings, zero after filter; no cache replay or sample fallback",
                len(raw),
            )
            return []

        replayed = self._replay_from_cache(limit)
        if replayed:
            return replayed

        live_requests_succeeded = self.http.successful_requests > successful_requests_before
        if live_requests_succeeded:
            LOGGER.warning(
                "Live sources returned %s raw internships but none passed filters; cache replay also empty",
                len(raw),
            )
            return []

        if self.allow_sample_fallback:
            LOGGER.warning("All live sources failed; using sample fallback (--allow-sample-fallback).")
            fallback = self._sample_internships()
            self._save_raw(fallback)
            return self.filter_internships(fallback)[:limit]

        LOGGER.warning(
            "All live sources failed and cache replay empty; enable --allow-sample-fallback for dev samples"
        )
        return []

    def filter_internships(self, internships: Iterable[Internship]) -> list[Internship]:
        filtered: list[Internship] = []
        for internship in internships:
            decision = self.filter_policy.evaluate(internship)
            LOGGER.info(
                "Filter decision=%s source=%s title=%r company=%r reason=%s",
                "accepted" if decision.accepted else "rejected",
                internship.source,
                internship.title,
                internship.company,
                decision.reason,
            )
            if decision.accepted:
                filtered.append(internship)
        return self._dedupe(filtered)

    def _discover_manual_urls(self, urls: list[str], limit: int) -> list[Internship]:
        internships: list[Internship] = []
        for url in urls:
            if not url:
                continue
            parsed = urlparse(url)
            if "greenhouse.io" in parsed.netloc:
                found = self.greenhouse.discover_url(url)
                source = "greenhouse_manual"
            elif "lever.co" in parsed.netloc:
                found = self.lever.discover_url(url)
                source = "lever_manual"
            else:
                found = self.company_careers.scrape_url(url, source="manual_url")
                source = "manual_url"
            LOGGER.info("Source=%s url=%s found=%s", source, url, len(found))
            internships.extend(found)
            if len(internships) >= limit:
                break
        return internships[:limit]

    @staticmethod
    def _discover_source(source: str, fetch: object) -> list[Internship]:
        try:
            found = fetch()
            LOGGER.info("Source=%s total_found=%s", source, len(found))
            return found
        except Exception as exc:
            LOGGER.warning("Source=%s failed gracefully: %s", source, exc)
            return []

    def _parse_seed_file(self, seed_file: Path | None) -> tuple[list[str], list[str], list[str]]:
        if not seed_file or not seed_file.exists():
            return [], [], []
        
        greenhouse_seeds: list[str] = []
        lever_seeds: list[str] = []
        manual_seeds: list[str] = []
        
        lines = seed_file.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("greenhouse:"):
                greenhouse_seeds.append(line.split(":", 1)[1].strip())
            elif line.startswith("lever:"):
                lever_seeds.append(line.split(":", 1)[1].strip())
            else:
                manual_seeds.append(line)
                
        return greenhouse_seeds, lever_seeds, manual_seeds

    def _search_queries(self) -> list[str]:
        policy = self.filter_policy
        if not policy.role_query:
            return DEFAULT_SEARCH_QUERIES
        query = f"{policy.role_query} india {policy.min_duration_months} months"
        if policy.ppo_required:
            query += " ppo"
        query += f" stipend {policy.min_stipend_inr}"
        return [query, *DEFAULT_SEARCH_QUERIES]

    def _replay_from_cache(self, limit: int) -> list[Internship]:
        cached = self._load_raw_cache()
        if not cached:
            LOGGER.info("No cached raw listings at %s", self.raw_output_path)
            return []
        LOGGER.info(
            "Post-filter live set empty; replaying %s cached listings from %s",
            len(cached),
            self.raw_output_path,
        )
        filtered = self.filter_internships(cached)
        if filtered:
            LOGGER.info("Cache replay filtered=%s", len(filtered))
            return filtered[:limit]
        LOGGER.warning("Cache replay produced zero matches with current filter policy")
        return []

    def _load_raw_cache(self) -> list[Internship]:
        if not self.raw_output_path.exists():
            return []
        try:
            payload = json.loads(self.raw_output_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            LOGGER.warning("Could not read cache %s: %s", self.raw_output_path, exc)
            return []
        if not isinstance(payload, list):
            return []
        internships: list[Internship] = []
        for item in payload:
            if isinstance(item, dict):
                internships.append(Internship(**item))
        return self._dedupe(internships)

    def _save_raw(self, internships: list[Internship]) -> None:
        if not internships:
            return
        self.raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(internship) for internship in self._dedupe(internships)]
        self.raw_output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        LOGGER.info("Saved raw internships count=%s path=%s", len(data), self.raw_output_path)

    @staticmethod
    def _dedupe(internships: Iterable[Internship]) -> list[Internship]:
        deduped: list[Internship] = []
        seen: set[tuple[str, str, str]] = set()
        for internship in internships:
            key = (
                internship.title.lower(),
                internship.company.lower(),
                internship.apply_url.lower(),
            )
            if not internship.title or key in seen:
                continue
            seen.add(key)
            deduped.append(internship)
        return deduped

    @staticmethod
    def _sample_internships() -> list[Internship]:
        return [
            Internship(
                title="AI Backend Intern",
                company="Sample Growth AI",
                location="Remote India",
                description=(
                    "6 months internship with INR 30000 monthly stipend. Build Python, FastAPI, "
                    "Docker, AWS, SQL and LLM-backed APIs. PPO and full-time conversion possible. "
                    "Company is scaling hiring for AI products."
                ),
                stipend_inr=30_000,
                duration_months=6,
                apply_url="https://example.com/sample-ai-backend-intern",
                source="sample_fallback",
                remote=True,
            ),
            Internship(
                title="Data Science Intern",
                company="Sample Analytics Labs",
                location="Bengaluru, India",
                description=(
                    "6 month data science internship with INR 25000 stipend. Work on Python, "
                    "Pandas, scikit-learn, SQL, dashboards, ML experimentation and model evaluation. "
                    "Strong performers considered for PPO."
                ),
                stipend_inr=25_000,
                duration_months=6,
                apply_url="https://example.com/sample-data-science-intern",
                source="sample_fallback",
                remote=False,
            ),
            Internship(
                title="Software Engineering Backend Intern",
                company="Sample SaaS Systems",
                location="Hyderabad, India",
                description=(
                    "Backend engineering intern for 6 months. INR 35000 monthly stipend. "
                    "Build REST APIs using Python, PostgreSQL, Redis, Docker, CI/CD and AWS. "
                    "Recurring internship hiring with full-time conversion track."
                ),
                stipend_inr=35_000,
                duration_months=6,
                apply_url="https://example.com/sample-backend-intern",
                source="sample_fallback",
                remote=False,
            ),
        ]
