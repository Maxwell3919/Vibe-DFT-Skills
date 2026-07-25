#!/usr/bin/env python3
"""Shared fail-closed matching for SIESTA FDF label families."""

from __future__ import annotations

import re


_OFFICIAL_FAMILY_VARIANTS = {
    "doskgrid?": frozenset(
        {"doskgridmonkhorstpack", "doskgridcutoff", "doskgridfile"}
    ),
    "ldoskgrid?": frozenset(
        {"ldoskgridmonkhorstpack", "ldoskgridcutoff", "ldoskgridfile"}
    ),
    "pdoskgrid?": frozenset(
        {"pdoskgridmonkhorstpack", "pdoskgridcutoff", "pdoskgridfile"}
    ),
}


def _normalized_label(value: str, *, preserve_family_marker: bool = False) -> str:
    allowed = r"[^a-z0-9?]+" if preserve_family_marker else r"[^a-z0-9]+"
    return re.sub(allowed, "", value.casefold())


def matches_official_label(value: str, official_label: str) -> bool:
    """Match exact labels and only the reviewed variants of manual ``?`` families."""
    normalized_value = _normalized_label(value)
    normalized_official = _normalized_label(
        official_label,
        preserve_family_marker=True,
    )
    if "?" not in normalized_official:
        return normalized_value == normalized_official
    return normalized_value in _OFFICIAL_FAMILY_VARIANTS.get(
        normalized_official,
        frozenset(),
    )
