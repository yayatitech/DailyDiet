"""Recipe catalog helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.models import RecipeCatalogEntry

_UNSAFE_STEM_CHARS = re.compile(r"[^A-Za-z0-9_-]+")
_MAX_IMAGE_STEM_LEN = 180


def sanitize_recipe_image_filename(
    uploaded_name: str | None,
    ext: str,
    recipe_id: int,
) -> str:
    """Safe basename for public/recipes/. Fallback is {recipe_id}{ext}."""
    fallback = f"{recipe_id}{ext}"
    if not uploaded_name or not uploaded_name.strip():
        return fallback

    raw = uploaded_name.replace("\\", "/").strip()
    base = Path(raw).name
    if not base or base in {".", ".."}:
        return fallback

    stem = Path(base).stem
    stem = _UNSAFE_STEM_CHARS.sub("-", stem)
    stem = re.sub(r"-{2,}", "-", stem).strip("-_.")
    if not stem:
        return fallback
    stem = stem[:_MAX_IMAGE_STEM_LEN].rstrip("-_.")
    if not stem:
        return fallback

    filename = f"{stem}{ext}"
    if Path(filename).name != filename:
        return fallback
    return filename


def recipe_stored_image_path(filename: str) -> str:
    return f"recipes/{filename}"


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
