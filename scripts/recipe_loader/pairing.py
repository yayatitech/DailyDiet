"""Pair ingredient/instruction screenshots by slug."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_SUFFIX_RE = re.compile(r"^(.+)__(ingredients|instructions)$", re.IGNORECASE)


@dataclass
class RecipeFiles:
    slug: str
    ingredients: Path | None = None
    instructions: Path | None = None

    def is_ready(self, *, allow_partial: bool = False) -> bool:
        if self.ingredients is None:
            return False
        if allow_partial:
            return True
        return self.instructions is not None


def parse_screenshot_path(path: Path) -> tuple[str, str] | None:
    """Return (slug, tab) for paths like slug__ingredients.png."""
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return None
    stem = path.stem
    match = _SUFFIX_RE.match(stem)
    if not match:
        return None
    return match.group(1), match.group(2).lower()


def scan_incoming(directory: Path) -> dict[str, RecipeFiles]:
    """Build slug -> RecipeFiles from all matching images in directory."""
    jobs: dict[str, RecipeFiles] = {}
    if not directory.is_dir():
        return jobs

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        parsed = parse_screenshot_path(path)
        if not parsed:
            continue
        slug, tab = parsed
        job = jobs.setdefault(slug, RecipeFiles(slug=slug))
        if tab == "ingredients":
            job.ingredients = path
        elif tab == "instructions":
            job.instructions = path
    return jobs


def read_name_override(incoming_dir: Path, slug: str) -> str | None:
    sidecar = incoming_dir / f"{slug}.name"
    if sidecar.is_file():
        text = sidecar.read_text(encoding="utf-8").strip()
        return text or None
    return None
