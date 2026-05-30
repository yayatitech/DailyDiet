"""Meal item parsing and recipe catalog lookup."""

from __future__ import annotations

import re

from app.schemas import MealItemOut

_WHITESPACE = re.compile(r"\s+")


def normalize_meal_name(name: str) -> str:
    return _WHITESPACE.sub(" ", name.strip().lower())


def split_slot_content(content: str) -> list[str]:
    if not content:
        return []
    return [line.strip() for line in content.split("\n") if line.strip()]


def join_slot_content(items: list[MealItemOut]) -> str:
    return "\n".join(item.text for item in items if item.text.strip())


def enrich_items(content: str, catalog: dict[str, str]) -> list[MealItemOut]:
    lines = split_slot_content(content)
    if not lines:
        return []
    return [
        MealItemOut(
            text=line,
            recipe_url=catalog.get(normalize_meal_name(line)),
        )
        for line in lines
    ]
