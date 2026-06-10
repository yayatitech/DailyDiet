"""Tesseract OCR + heuristic parsing."""

from __future__ import annotations

import re
from pathlib import Path

import sys_path  # noqa: F401

from normalize import slug_to_default_name

from .base import RecipeDraft

_INGREDIENT_LINE = re.compile(
    r"^[\d./\s]+(?:cup|cups|tbsp|tsp|g|kg|ml|oz)?\s+.+",
    re.IGNORECASE,
)
_AMOUNT_ITEM = re.compile(
    r"^([\d./]+\s*(?:cup|cups|tbsp|tsp|g|kg|ml|oz)?)\s+(.+)$",
    re.IGNORECASE,
)
_STEP_LINE = re.compile(r"^\s*(?:\d+[\.\):]|\u2022|-)\s*(.+)", re.UNICODE)
_SKIP_LINE = re.compile(
    r"^(ingredients|instructions|recipe|cooking time|mins|min\b|\d+\s*mins)",
    re.IGNORECASE,
)


def _ocr_image(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "OCR requires: pip install -r requirements-ocr.txt and apt install tesseract-ocr"
        ) from e

    with Image.open(path) as img:
        return pytesseract.image_to_string(img.convert("RGB"))


def parse_ingredient_line(line: str) -> dict[str, str] | None:
    line = line.strip().lstrip("\u2022\u25c6\u25aa-* ").strip()
    if not line or _SKIP_LINE.match(line):
        return None
    match = _AMOUNT_ITEM.match(line)
    if match:
        return {"amount": match.group(1).strip(), "item": match.group(2).strip()}
    if _INGREDIENT_LINE.match(line):
        parts = line.split(None, 1)
        if len(parts) == 2:
            return {"amount": parts[0], "item": parts[1]}
    return None


def _parse_ingredients_text(text: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for line in text.splitlines():
        parsed = parse_ingredient_line(line)
        if parsed:
            result.append(parsed)
    return result


def _parse_instructions_text(text: str) -> str:
    steps: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or _SKIP_LINE.match(line):
            continue
        step_match = _STEP_LINE.match(line)
        if step_match:
            steps.append(step_match.group(1).strip())
        elif len(line) > 20 and not _INGREDIENT_LINE.match(line):
            steps.append(line)
    return "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps)) if steps else ""


def _guess_title(text: str, default: str) -> str:
    for line in text.splitlines()[:8]:
        line = line.strip()
        if not line or _SKIP_LINE.match(line) or len(line) < 4:
            continue
        if len(line) < 80 and not _INGREDIENT_LINE.match(line):
            return line
    return default


class OcrExtractor:
    def extract(
        self,
        slug: str,
        ingredients_path: Path,
        instructions_path: Path | None,
        name_override: str | None,
    ) -> RecipeDraft:
        default_name = name_override or slug_to_default_name(slug)
        ing_text = _ocr_image(ingredients_path)
        ingredients = _parse_ingredients_text(ing_text)
        name = _guess_title(ing_text, default_name)

        instructions = ""
        if instructions_path and instructions_path.is_file():
            inst_text = _ocr_image(instructions_path)
            instructions = _parse_instructions_text(inst_text)
            if name == default_name:
                title = _guess_title(inst_text, default_name)
                if title != default_name:
                    name = title

        return RecipeDraft(
            name=name,
            display_name=name,
            ingredients=ingredients,
            instructions=instructions,
            extractor="ocr",
        )
