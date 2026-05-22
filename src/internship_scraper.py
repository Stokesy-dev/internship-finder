from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from .company_careers_scraper import CompanyCareersScraper
from .greenhouse_scraper import GreenhouseScraper
from .lever_scraper import LeverScraper
from .models import Internship
from .scraper_http import ScraperHttpClient
from .text_utils import has_role_match, is_remote_or_india
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
        raw_output_path: str | Path = "data/internships.json",
        timeout_seconds: int = 15,
        retries: int = 2,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self.min_stipend_inr = min_stipend_inr
        self.min_duration_months = min_duration_months
        self.role_query = role_query
        self.ppo_required = ppo_required
        self.live_only = live_only
        self.raw_output_path = Path(raw_output_path)
        self.http = ScraperHttpClient(
            timeout_seconds=timeout_seconds,
            retries=retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        self.greenhouse = GreenhouseScraper(self.http)
        self.lever = LeverScraper(self.http)
        self.wellfound = WellfoundScraper(self.http)
        self.company_careers = CompanyCareersScraper(self.http)

    def discover(self, limit: int = 50, manual_urls: list[str] | None = None) -> list[Internship]:
        successful_requests_before = self.http.successful_requests
        discovered: list[Internship] = []
        manual = self._discover_manual_urls(manual_urls or [], limit)
        discovered.extend(manual)
        discovered.extend(self._discover_source("greenhouse", lambda: self.greenhouse.discover(limit=limit)))
        discovered.extend(self._discover_source("lever", lambda: self.lever.discover(limit=limit)))
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
        self._save_raw(raw)
        filtered = self.filter_internships(raw)
        if filtered:
            LOGGER.info("Discovery complete raw=%s filtered=%s", len(raw), len(filtered))
            return filtered[:limit]

        live_requests_succeeded = self.http.successful_requests > successful_requests_before
        if raw:
            LOGGER.warning("Live sources returned %s internships but none passed filters. Fallback disabled.", len(raw))
            return []
        if self.live_only:
            LOGGER.error("--live enabled and all live sources failed or returned zero internships. No fallback used.")
            return []
        if live_requests_succeeded:
            LOGGER.warning("Live sources responded but returned zero internships. Fallback disabled.")
            return []

        LOGGER.warning("All live sources failed; using sample fallback data.")
        fallback = self._sample_internships()
        self._save_raw(fallback)
        return self.filter_internships(fallback)[:limit]

    def filter_internships(self, internships: Iterable[Internship]) -> list[Internship]:
        filtered: list[Internship] = []
        for internship in internships:
            accepted, reason = self._filter_decision(internship)
            LOGGER.info(
                "Filter decision=%s source=%s title=%r company=%r reason=%s",
                "accepted" if accepted else "rejected",
                internship.source,
                internship.title,
                internship.company,
                reason,
            )
            if accepted:
                filtered.append(internship)
        return self._dedupe(filtered)

    def _filter_decision(self, internship: Internship) -> tuple[bool, str]:
        text = f"{internship.title} {internship.description}"
        if internship.stipend_inr < self.min_stipend_inr:
            return False, f"stipend {internship.stipend_inr} < {self.min_stipend_inr}"
        if internship.duration_months < self.min_duration_months:
            return False, f"duration {internship.duration_months} < {self.min_duration_months}"
        if self.role_query and not _role_query_match(text, self.role_query):
            return False, f"role does not match {self.role_query!r}"
        if self.ppo_required and not _has_ppo_signal(text):
            return False, "missing PPO/full-time conversion signal"
        if not has_role_match(text):
            return False, "missing target AI/DS/SWE/backend role keyword"
        if not is_remote_or_india(internship.location, internship.description):
            return False, "not remote or India"
        return True, "passes all filters"

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

    def _search_queries(self) -> list[str]:
        if not self.role_query:
            return DEFAULT_SEARCH_QUERIES
        query = f"{self.role_query} india {self.min_duration_months} months"
        if self.ppo_required:
            query += " ppo"
        query += f" stipend {self.min_stipend_inr}"
        return [query, *DEFAULT_SEARCH_QUERIES]

    def _save_raw(self, internships: list[Internship]) -> None:
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


def _role_query_match(text: str, role_query: str) -> bool:
    text_tokens = set(re.findall(r"[a-z0-9+#.]+", text.lower()))
    query_tokens = [
        token
        for token in re.findall(r"[a-z0-9+#.]+", role_query.lower())
        if token not in {"role", "job", "position"}
    ]
    return all(token in text_tokens for token in query_tokens)


def _has_ppo_signal(text: str) -> bool:
    lowered = text.lower()
    return any(
        signal in lowered
        for signal in [
            "ppo",
            "pre-placement",
            "pre placement",
            "full-time conversion",
            "full time conversion",
            "conversion track",
            "considered for full-time",
            "considered for full time",
        ]
    )
