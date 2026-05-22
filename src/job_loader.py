from __future__ import annotations

from pathlib import Path

import pandas as pd

from .internship_scraper import InternshipScraper
from .models import Internship
from .text_utils import clean_text, parse_duration_months, parse_money_inr


class InternshipRepository:
    def __init__(
        self,
        scraper: InternshipScraper | None = None,
        min_stipend_inr: int = 20_000,
        min_duration_months: int = 6,
        role_query: str = "",
        ppo_required: bool = False,
        live_only: bool = False,
    ) -> None:
        self.scraper = scraper or InternshipScraper(
            min_stipend_inr=min_stipend_inr,
            min_duration_months=min_duration_months,
            role_query=role_query,
            ppo_required=ppo_required,
            live_only=live_only,
        )

    def load(
        self,
        limit: int,
        jobs_csv: Path | None = None,
        internship_urls: list[str] | tuple[str, ...] | None = None,
    ) -> list[Internship]:
        if jobs_csv:
            return self._load_csv(jobs_csv, limit)
        return self.scraper.discover(limit, manual_urls=list(internship_urls or []))

    def _load_csv(self, csv_path: Path, limit: int) -> list[Internship]:
        frame = pd.read_csv(csv_path).head(limit)
        internships = [self._from_row(row) for row in frame.to_dict(orient="records")]
        return self.scraper.filter_internships(internships)

    @staticmethod
    def _from_row(row: dict) -> Internship:
        title = clean_text(str(row.get("title") or row.get("role") or ""))
        company = clean_text(str(row.get("company") or "Unknown"))
        description = clean_text(str(row.get("description") or row.get("jd") or ""))
        return Internship(
            title=title,
            company=company,
            location=clean_text(str(row.get("location") or "")),
            description=description,
            stipend_inr=_int_or_parse(row.get("stipend_inr"), description),
            duration_months=_int_or_parse(row.get("duration_months"), description, duration=True),
            apply_url=str(row.get("apply_url") or row.get("url") or ""),
            source=str(row.get("source") or "csv"),
            remote="remote" in f"{row.get('location', '')} {description}".lower(),
            posted_at=str(row.get("posted_at") or ""),
            metadata=row,
        )


def _int_or_parse(value: object, text: str, duration: bool = False) -> int:
    try:
        if pd.notna(value) and str(value).strip():
            return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        pass
    combined = f"{value or ''} {text}"
    return parse_duration_months(combined) if duration else parse_money_inr(combined)
