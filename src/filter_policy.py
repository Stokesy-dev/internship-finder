from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .models import Internship
from .text_utils import has_role_match, is_remote_or_india

FilterMode = Literal["strict", "lenient"]


@dataclass(frozen=True, slots=True)
class FilterDecision:
    accepted: bool
    reason: str
    penalties: dict[str, bool] = field(default_factory=dict)


class FilterPolicy:
    """Stipend, duration, role, geo, and optional PPO hard-filter rules."""

    def __init__(
        self,
        mode: FilterMode = "strict",
        min_stipend_inr: int = 20_000,
        min_duration_months: int = 6,
        role_query: str = "",
        ppo_required: bool = False,
    ) -> None:
        self.mode = mode
        self.min_stipend_inr = min_stipend_inr
        self.min_duration_months = min_duration_months
        self.role_query = role_query
        self.ppo_required = ppo_required

    def evaluate(self, internship: Internship) -> FilterDecision:
        text = f"{internship.title} {internship.description}"
        penalties: dict[str, bool] = {}

        stipend_ok, stipend_reason = self._stipend_decision(internship.stipend_inr)
        if not stipend_ok:
            return FilterDecision(False, stipend_reason, penalties)
        if internship.stipend_inr <= 0 and self.mode == "lenient":
            penalties["stipend_unknown"] = True

        duration_ok, duration_reason = self._duration_decision(internship.duration_months)
        if not duration_ok:
            return FilterDecision(False, duration_reason, penalties)
        if internship.duration_months <= 0 and self.mode == "lenient":
            penalties["duration_unknown"] = True

        if self.role_query and not _role_query_match(text, self.role_query):
            return FilterDecision(False, f"role does not match {self.role_query!r}", penalties)
        if self.ppo_required and not _has_ppo_signal(text):
            return FilterDecision(False, "missing PPO/full-time conversion signal", penalties)
        if not has_role_match(text):
            return FilterDecision(False, "missing target AI/DS/SWE/backend role keyword", penalties)
        if not is_remote_or_india(internship.location, internship.description):
            return FilterDecision(False, "not remote or India", penalties)

        reason = "passes all filters"
        if penalties:
            unknown = [key.replace("_unknown", "") for key in penalties]
            reason = f"passes all filters (unknown: {', '.join(unknown)})"
        return FilterDecision(True, reason, penalties)

    def _stipend_decision(self, stipend_inr: int) -> tuple[bool, str]:
        if stipend_inr <= 0:
            if self.mode == "lenient":
                return True, "stipend unknown (lenient pass)"
            return False, f"stipend unknown (strict requires >= {self.min_stipend_inr})"
        if stipend_inr < self.min_stipend_inr:
            return False, f"stipend {stipend_inr} < {self.min_stipend_inr}"
        return True, "stipend ok"

    def _duration_decision(self, duration_months: int) -> tuple[bool, str]:
        if duration_months <= 0:
            if self.mode == "lenient":
                return True, "duration unknown (lenient pass)"
            return False, f"duration unknown (strict requires >= {self.min_duration_months} months)"
        if duration_months < self.min_duration_months:
            return False, f"duration {duration_months} < {self.min_duration_months}"
        return True, "duration ok"


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
