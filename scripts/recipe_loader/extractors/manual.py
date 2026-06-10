"""Manual extractor — scaffold only, no text extraction."""

from __future__ import annotations

from pathlib import Path

import sys_path  # noqa: F401

from normalize import slug_to_default_name

from .base import RecipeDraft


class ManualExtractor:
    def extract(
        self,
        slug: str,
        ingredients_path: Path,
        instructions_path: Path | None,
        name_override: str | None,
    ) -> RecipeDraft:
        name = (name_override or slug_to_default_name(slug)).strip()
        return RecipeDraft(
            name=name,
            display_name=name,
            ingredients=[],
            instructions="",
            extractor="manual",
        )
