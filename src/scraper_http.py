from __future__ import annotations

import json
import logging
import time

import requests

LOGGER = logging.getLogger(__name__)


class ScraperHttpClient:
    def __init__(
        self,
        timeout_seconds: int = 15,
        retries: int = 2,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.successful_requests = 0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0 Safari/537.36"
                ),
                "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
            }
        )

    def get_text(self, url: str, source: str, accept_json: bool = False) -> str:
        headers = {"Accept": "application/json"} if accept_json else None
        LOGGER.info("Querying source=%s url=%s", source, url)
        for attempt in range(1, self.retries + 2):
            try:
                response = self.session.get(url, timeout=self.timeout_seconds, headers=headers)
                if response.status_code in {403, 404}:
                    LOGGER.warning("Source=%s url=%s status=%s", source, url, response.status_code)
                    return ""
                response.raise_for_status()
                self.successful_requests += 1
                return response.text
            except requests.RequestException as exc:
                if attempt > self.retries:
                    LOGGER.warning("Source=%s url=%s failed: %s", source, url, exc)
                    return ""
                LOGGER.info("Retrying source=%s url=%s attempt=%s", source, url, attempt + 1)
                time.sleep(self.retry_backoff_seconds * attempt)
        return ""

    def get_json(self, url: str, source: str) -> object:
        text = self.get_text(url, source=source, accept_json=True)
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            LOGGER.warning("Source=%s url=%s returned invalid JSON: %s", source, url, exc)
            return {}
