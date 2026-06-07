"""Name normalization — mirrors backend app.meals.normalize_meal_name."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_name_key(name: str) -> str:
    return _WHITESPACE.sub(" ", name.strip().lower())


def slug_to_default_name(slug: str) -> str:
    """Convert job slug to a human-readable default catalog name."""
    return _WHITESPACE.sub(" ", slug.replace("-", " ").replace("_", " ")).strip().title()
