from __future__ import annotations

import logging
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Internship
from .scraper_http import ScraperHttpClient
from .text_utils import clean_text, parse_duration_months, parse_money_inr

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://internshala.com"

# Polite scraping: ~1s between search page requests (see docs/CLI.md).
DEFAULT_REQUEST_DELAY_SECONDS = 1.0

DEFAULT_SEARCH_SLUGS = [
    "python-internship",
    "machine-learning-internship",
    "data-science-internship",
    "backend-development-internship",
    "artificial-intelligence-internship",
]


class InternshalaScraper:
    source = "internshala"

    def __init__(
        self,
        http: ScraperHttpClient,
        request_delay_seconds: float = DEFAULT_REQUEST_DELAY_SECONDS,
    ) -> None:
        self.http = http
        self.request_delay_seconds = request_delay_seconds

    def discover(
        self,
        slugs: list[str] | None = None,
        limit: int = 50,
    ) -> list[Internship]:
        internships: list[Internship] = []
        for index, slug in enumerate(slugs or DEFAULT_SEARCH_SLUGS):
            if index > 0 and self.request_delay_seconds > 0:
                time.sleep(self.request_delay_seconds)
            url = f"{BASE_URL}/internships/{slug}/"
            found = self.scrape_search_page(url)
            LOGGER.info("Source=%s slug=%s found=%s", self.source, slug, len(found))
            internships.extend(found)
            if len(internships) >= limit:
                break
        return internships[:limit]

    def scrape_search_page(self, url: str) -> list[Internship]:
        html = self.http.get_text(url, source=self.source)
        if not html:
            return []
        return parse_internshala_listing_html(html, base_url=BASE_URL)


def parse_internshala_listing_html(html: str, base_url: str = BASE_URL) -> list[Internship]:
    soup = BeautifulSoup(html, "html.parser")
    internships: list[Internship] = []
    for card in soup.select("div.individual_internship"):
        parsed = _parse_card(card, base_url)
        if parsed:
            internships.append(parsed)
    return internships


def _parse_card(card: BeautifulSoup, base_url: str) -> Internship | None:
    title_el = card.select_one("a.job-title-href")
    title = clean_text(title_el.get_text(" ") if title_el else "")
    if not title:
        return None

    company_el = card.select_one("p.company-name")
    company = clean_text(company_el.get_text(" ") if company_el else "Unknown")

    location = _parse_location(card)
    stipend_text = _parse_stipend_text(card)
    duration_text = _parse_duration_text(card)
    about = card.select_one("div.about_job")
    about_text = clean_text(about.get_text(" ") if about else "")
    skills = _parse_skill_tags(card)
    description = clean_text(
        f"{title} internship at {company} in {location}. {about_text} Skills: {', '.join(skills)}"
    )
    if stipend_text:
        description = f"{description} Stipend: {stipend_text}."
    if duration_text:
        description = f"{description} Duration: {duration_text}."

    apply_path = (
        str(card.get("data-href") or "")
        or (title_el.get("href") if title_el else "")
        or ""
    )
    apply_url = urljoin(base_url, apply_path) if apply_path else ""

    return Internship(
        title=title,
        company=company,
        location=location,
        description=description[:8000],
        stipend_inr=parse_money_inr(stipend_text or description),
        duration_months=parse_duration_months(duration_text or description),
        apply_url=apply_url,
        source="internshala",
        remote=_is_work_from_home(location, description),
        metadata={
            "stipend_text": stipend_text,
            "duration_text": duration_text,
            "skills": skills,
        },
    )


def _parse_location(card: BeautifulSoup) -> str:
    loc = card.select_one("div.row-1-item.locations span")
    if not loc:
        return "India"
    parts = [clean_text(a.get_text(" ")) for a in loc.find_all("a")]
    text = clean_text(loc.get_text(" "))
    if parts:
        base = ", ".join(parts)
        suffix = text.replace(base, "").strip()
        return clean_text(f"{base} {suffix}")
    return text or "India"


def _parse_stipend_text(card: BeautifulSoup) -> str:
    stipend = card.select_one("span.stipend")
    return clean_text(stipend.get_text(" ") if stipend else "")


def _parse_duration_text(card: BeautifulSoup) -> str:
    for row in card.select("div.row-1-item"):
        text = clean_text(row.get_text(" "))
        if re.search(r"\d+\s*months?", text, re.I):
            return text
    return ""


def _parse_skill_tags(card: BeautifulSoup) -> list[str]:
    tags: list[str] = []
    for anchor in card.select("a[data-popup_delay]"):
        label = clean_text(anchor.get_text(" "))
        if label and label not in tags:
            tags.append(label)
    return tags[:12]


def _is_work_from_home(location: str, description: str) -> bool:
    haystack = f"{location} {description}".lower()
    return "work from home" in haystack or "wfh" in haystack or "remote" in haystack
