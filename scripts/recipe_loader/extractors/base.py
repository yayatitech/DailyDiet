"""Shared types for extraction backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class RecipeDraft:
    name: str
    display_name: str | None = None
    ingredients: list[dict[str, str]] = field(default_factory=list)
    instructions: str = ""
    extractor: str = ""

    def to_payload(self, slug: str, image_file: str, source_screenshots: list[str]) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "image_file": image_file,
            "source_screenshots": source_screenshots,
            "extractor": self.extractor,
            "slug": slug,
        }


class Extractor(Protocol):
    def extract(
        self,
        slug: str,
        ingredients_path: Path,
        instructions_path: Path | None,
        name_override: str | None,
    ) -> RecipeDraft: ...
