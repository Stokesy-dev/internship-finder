from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .filter_policy import FilterMode

RunProfileName = Literal["discover", "shortlist"]


@dataclass(frozen=True, slots=True)
class RunProfileDefaults:
    filter_mode: FilterMode
    rich_reports: bool
    limit: int
    top_k: int


_PROFILES: dict[RunProfileName, RunProfileDefaults] = {
    "discover": RunProfileDefaults(
        filter_mode="lenient",
        rich_reports=False,
        limit=30,
        top_k=10,
    ),
    "shortlist": RunProfileDefaults(
        filter_mode="strict",
        rich_reports=True,
        limit=30,
        top_k=5,
    ),
}


def profile_defaults(command: RunProfileName) -> RunProfileDefaults:
    try:
        return _PROFILES[command]
    except KeyError as exc:
        raise ValueError(f"Unknown run profile: {command!r}") from exc


def resolve_filter_mode(
    profile: RunProfileDefaults,
    *,
    lenient: bool | None,
) -> FilterMode:
    if lenient is True:
        return "lenient"
    if lenient is False:
        return "strict"
    return profile.filter_mode


def resolve_rich_reports(
    profile: RunProfileDefaults,
    *,
    rich_reports: bool | None,
) -> bool:
    if rich_reports is not None:
        return rich_reports
    return profile.rich_reports
