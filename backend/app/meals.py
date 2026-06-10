"""Meal item parsing and recipe catalog lookup."""

from __future__ import annotations

import re

from app.recipe_utils import RecipeLookup, resolve_meal_recipe_link
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


def enrich_items(content: str, catalog: dict[str, RecipeLookup]) -> list[MealItemOut]:
    lines = split_slot_content(content)
    if not lines:
        return []
    items: list[MealItemOut] = []
    for line in lines:
        lookup = catalog.get(normalize_meal_name(line))
        if not lookup:
            items.append(MealItemOut(text=line))
            continue
        recipe_id, recipe_url, recipe_external = resolve_meal_recipe_link(lookup)
        items.append(
            MealItemOut(
                text=line,
                recipe_id=recipe_id,
                recipe_url=recipe_url,
                recipe_external=recipe_external,
            )
        )
    return items
