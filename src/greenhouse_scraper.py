from __future__ import annotations

import logging
import re

from .company_careers_scraper import html_to_text, infer_location
from .models import Internship
from .scraper_http import ScraperHttpClient
from .text_utils import clean_text, parse_duration_months, parse_money_inr

LOGGER = logging.getLogger(__name__)

DEFAULT_GREENHOUSE_BOARDS = ["razorpay", "slice", "meesho", "atlan", "browserstack"]


class GreenhouseScraper:
    source = "greenhouse"

    def __init__(self, http: ScraperHttpClient) -> None:
        self.http = http

    def discover(self, boards: list[str] | None = None, limit: int = 50) -> list[Internship]:
        internships: list[Internship] = []
        for board in boards or DEFAULT_GREENHOUSE_BOARDS:
            found = self.fetch_board(board)
            LOGGER.info("Source=%s board=%s found=%s", self.source, board, len(found))
            internships.extend(found)
            if len(internships) >= limit:
                break
        return internships[:limit]

    def discover_url(self, url: str) -> list[Internship]:
        board = board_from_url(url)
        if not board:
            return []
        return self.fetch_board(board)

    def fetch_board(self, board: str) -> list[Internship]:
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
        payload = self.http.get_json(api_url, source=self.source)
        jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
        internships: list[Internship] = []
        for job in jobs:
            title = clean_text(str(job.get("title") or ""))
            content = html_to_text(str(job.get("content") or ""))
            location = clean_text(str((job.get("location") or {}).get("name") or ""))
            description = clean_text(f"{content} {title}")
            if "intern" not in title.lower() and "intern" not in description.lower():
                continue
            internships.append(
                Internship(
                    title=title,
                    company=board,
                    location=location or infer_location(description),
                    description=description,
                    stipend_inr=parse_money_inr(description),
                    duration_months=parse_duration_months(description),
                    apply_url=str(job.get("absolute_url") or ""),
                    source=self.source,
                    remote="remote" in f"{location} {description}".lower(),
                    metadata={"board": board, "id": job.get("id")},
                )
            )
        return internships


def board_from_url(url: str) -> str:
    match = re.search(r"greenhouse\.io/(?:embed/)?(?:job_board\?for=)?([^/?#]+)", url)
    return match.group(1) if match else ""
