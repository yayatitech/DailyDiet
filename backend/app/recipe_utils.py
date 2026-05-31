"""Recipe catalog helpers."""

from __future__ import annotations

from dataclasses import dataclass

from app.models import RecipeCatalogEntry


def recipe_image_url(image_path: str | None) -> str | None:
    if not image_path:
        return None
    return f"/static/{image_path.lstrip('/')}"


def recipe_has_internal_content(entry: RecipeCatalogEntry) -> bool:
    if entry.image_path:
        return True
    if entry.instructions and entry.instructions.strip():
        return True
    ingredients = entry.ingredients or []
    return isinstance(ingredients, list) and len(ingredients) > 0


@dataclass(frozen=True)
class RecipeLookup:
    id: int
    external_url: str | None
    has_internal: bool


def recipe_lookup_from_entry(entry: RecipeCatalogEntry) -> RecipeLookup:
    return RecipeLookup(
        id=entry.id,
        external_url=entry.external_url.strip() if entry.external_url else None,
        has_internal=recipe_has_internal_content(entry),
    )


def resolve_meal_recipe_link(lookup: RecipeLookup) -> tuple[int | None, str | None, bool]:
    if lookup.has_internal:
        return lookup.id, f"/recipes/{lookup.id}", False
    if lookup.external_url:
        return lookup.id, lookup.external_url, True
    return None, None, False
