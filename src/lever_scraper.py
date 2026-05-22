from __future__ import annotations

import logging
import re

from .company_careers_scraper import html_to_text, infer_location
from .models import Internship
from .scraper_http import ScraperHttpClient
from .text_utils import clean_text, parse_duration_months, parse_money_inr

LOGGER = logging.getLogger(__name__)

DEFAULT_LEVER_BOARDS = ["postman", "zeta", "groww", "cred", "smallcase"]


class LeverScraper:
    source = "lever"

    def __init__(self, http: ScraperHttpClient) -> None:
        self.http = http

    def discover(self, companies: list[str] | None = None, limit: int = 50) -> list[Internship]:
        internships: list[Internship] = []
        for company in companies or DEFAULT_LEVER_BOARDS:
            found = self.fetch_company(company)
            LOGGER.info("Source=%s company=%s found=%s", self.source, company, len(found))
            internships.extend(found)
            if len(internships) >= limit:
                break
        return internships[:limit]

    def discover_url(self, url: str) -> list[Internship]:
        company = company_from_url(url)
        if not company:
            return []
        return self.fetch_company(company)

    def fetch_company(self, company: str) -> list[Internship]:
        api_url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        payload = self.http.get_json(api_url, source=self.source)
        jobs = payload if isinstance(payload, list) else []
        internships: list[Internship] = []
        for job in jobs:
            title = clean_text(str(job.get("text") or ""))
            description = _description(job)
            location = clean_text(str((job.get("categories") or {}).get("location") or ""))
            if "intern" not in title.lower() and "intern" not in description.lower():
                continue
            internships.append(
                Internship(
                    title=title,
                    company=company,
                    location=location or infer_location(description),
                    description=description,
                    stipend_inr=parse_money_inr(description),
                    duration_months=parse_duration_months(description),
                    apply_url=str(job.get("hostedUrl") or job.get("applyUrl") or ""),
                    source=self.source,
                    remote="remote" in f"{location} {description}".lower(),
                    posted_at=str(job.get("createdAt") or ""),
                    metadata={"company": company, "id": job.get("id")},
                )
            )
        return internships


def company_from_url(url: str) -> str:
    match = re.search(r"jobs\.lever\.co/([^/?#]+)", url)
    return match.group(1) if match else ""


def _description(job: dict) -> str:
    parts: list[str] = [str(job.get("descriptionPlain") or job.get("description") or "")]
    for list_item in job.get("lists") or []:
        if isinstance(list_item, dict):
            parts.append(str(list_item.get("text") or ""))
            parts.extend(str(content) for content in list_item.get("content") or [])
    return html_to_text(" ".join(parts))
