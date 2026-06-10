"""Extractor factory — switch between llm, ocr, and manual."""

from __future__ import annotations

import os

from .base import Extractor
from .llm import LlmExtractor
from .manual import ManualExtractor
from .ocr import OcrExtractor

_EXTRACTORS: dict[str, type] = {
    "llm": LlmExtractor,
    "ocr": OcrExtractor,
    "manual": ManualExtractor,
}


def get_extractor(name: str | None = None) -> Extractor:
    key = (name or os.environ.get("RECIPE_EXTRACTOR") or "llm").strip().lower()
    if key not in _EXTRACTORS:
        raise ValueError(f"Unknown extractor {key!r}; choose from: {', '.join(_EXTRACTORS)}")
    return _EXTRACTORS[key]()  # type: ignore[return-value]
