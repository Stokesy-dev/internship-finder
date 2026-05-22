from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import Internship
from .scraper_http import ScraperHttpClient
from .text_utils import clean_text, parse_duration_months, parse_money_inr

LOGGER = logging.getLogger(__name__)

DEFAULT_CAREERS_PAGES = [
    "https://www.razorpay.com/jobs/",
    "https://www.atlan.com/careers/",
    "https://www.browserstack.com/careers",
]


class CompanyCareersScraper:
    source = "company_careers"

    def __init__(self, http: ScraperHttpClient) -> None:
        self.http = http

    def discover(self, urls: list[str] | None = None, limit: int = 50) -> list[Internship]:
        internships: list[Internship] = []
        for url in urls or DEFAULT_CAREERS_PAGES:
            internships.extend(self.scrape_url(url, source=self.source))
            LOGGER.info("Source=%s url=%s found=%s", self.source, url, len(internships))
            if len(internships) >= limit:
                break
        return internships[:limit]

    def scrape_url(self, url: str, source: str = "manual_url") -> list[Internship]:
        html = self.http.get_text(url, source=source)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        internships = _internships_from_links(soup, url, source)
        if internships:
            return internships
        page_text = clean_text(soup.get_text(" "))
        if "intern" not in page_text.lower():
            return []
        return [
            Internship(
                title=_infer_title(page_text),
                company=company_from_url(url),
                location=infer_location(page_text),
                description=page_text[:5000],
                stipend_inr=parse_money_inr(page_text),
                duration_months=parse_duration_months(page_text),
                apply_url=url,
                source=source,
                remote="remote" in page_text.lower(),
                metadata={"url": url},
            )
        ]


def html_to_text(html: str) -> str:
    return clean_text(BeautifulSoup(html, "html.parser").get_text(" "))


def company_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host.split(".")[0].replace("-", " ").title() if host else "Unknown"


def infer_location(text: str) -> str:
    lowered = text.lower()
    if "remote" in lowered and "india" in lowered:
        return "Remote India"
    if "remote" in lowered:
        return "Remote"
    for city in ["Bengaluru", "Bangalore", "Mumbai", "Pune", "Delhi", "Gurugram", "Hyderabad", "Chennai", "Noida"]:
        if city.lower() in lowered:
            return f"{city}, India"
    if "india" in lowered:
        return "India"
    return ""


def _internships_from_links(soup: BeautifulSoup, base_url: str, source: str) -> list[Internship]:
    internships: list[Internship] = []
    page_text = clean_text(soup.get_text(" "))
    for anchor in soup.find_all("a", href=True):
        anchor_text = clean_text(anchor.get_text(" "))
        href = str(anchor.get("href") or "")
        if not anchor_text or "intern" not in anchor_text.lower():
            continue
        surrounding = clean_text(anchor.parent.get_text(" ") if anchor.parent else anchor_text)
        description = clean_text(f"{anchor_text} {surrounding} {page_text[:1500]}")
        internships.append(
            Internship(
                title=anchor_text[:160],
                company=company_from_url(base_url),
                location=infer_location(description),
                description=description[:5000],
                stipend_inr=parse_money_inr(description),
                duration_months=parse_duration_months(description),
                apply_url=urljoin(base_url, href),
                source=source,
                remote="remote" in description.lower(),
                metadata={"base_url": base_url},
            )
        )
    return internships


def _infer_title(text: str) -> str:
    match = re.search(r"([A-Za-z /+-]{0,60}intern[A-Za-z /+-]{0,80})", text, flags=re.IGNORECASE)
    return clean_text(match.group(1)).title() if match else "Internship"
