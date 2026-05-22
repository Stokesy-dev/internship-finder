from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

from .company_careers_scraper import company_from_url, infer_location
from .models import Internship
from .scraper_http import ScraperHttpClient
from .text_utils import clean_text, parse_duration_months, parse_money_inr

LOGGER = logging.getLogger(__name__)

DEFAULT_SEARCH_QUERIES = [
    "ai intern india 6 months stipend",
    "machine learning intern remote india ppo",
    "data science intern india 6 months",
    "backend intern india stipend ppo",
]


class WellfoundScraper:
    source = "wellfound"

    def __init__(self, http: ScraperHttpClient) -> None:
        self.http = http

    def discover(self, queries: list[str] | None = None, limit: int = 50) -> list[Internship]:
        internships: list[Internship] = []
        for query in queries or DEFAULT_SEARCH_QUERIES:
            url = f"https://wellfound.com/jobs?keywords={requests.utils.quote(query)}"
            found = self.scrape_search_url(url)
            LOGGER.info("Source=%s query=%r found=%s", self.source, query, len(found))
            internships.extend(found)
            if len(internships) >= limit:
                break
        return internships[:limit]

    def scrape_search_url(self, url: str) -> list[Internship]:
        html = self.http.get_text(url, source=self.source)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        page_text = clean_text(soup.get_text(" "))
        internships: list[Internship] = []
        for anchor in soup.find_all("a", href=True):
            title = clean_text(anchor.get_text(" "))
            href = str(anchor.get("href") or "")
            if "intern" not in title.lower():
                continue
            surrounding = clean_text(anchor.parent.get_text(" ") if anchor.parent else title)
            description = clean_text(f"{title} {surrounding} {page_text[:1500]}")
            internships.append(
                Internship(
                    title=title[:160],
                    company=company_from_url(url),
                    location=infer_location(description),
                    description=description[:5000],
                    stipend_inr=parse_money_inr(description),
                    duration_months=parse_duration_months(description),
                    apply_url=requests.compat.urljoin(url, href),
                    source=self.source,
                    remote="remote" in description.lower(),
                    metadata={"search_url": url},
                )
            )
        return internships
