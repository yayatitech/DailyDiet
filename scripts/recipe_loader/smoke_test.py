#!/usr/bin/env python3
"""Quick smoke test for recipe_loader (ops only)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import sys_path  # noqa: F401
from crop import crop_hero_image
from extractors import get_extractor
from normalize import normalize_name_key, slug_to_default_name
from pairing import parse_screenshot_path, scan_incoming
from paths import ensure_dirs
from PIL import Image

ROOT = Path(__file__).resolve().parent


def _make_screenshot(path: Path, color: tuple[int, int, int]) -> None:
    img = Image.new("RGB", (400, 800), color)
    img.save(path)


def main() -> int:
    assert normalize_name_key("Pumkin  Aloo  Tikki") == "pumkin aloo tikki"
    assert parse_screenshot_path(Path("x__ingredients.png")) == ("x", "ingredients", 0)
    assert parse_screenshot_path(Path("x__ingredients.PNG")) == ("x", "ingredients", 0)
    assert parse_screenshot_path(Path("Wheat_Upama__ingredients__01.png")) == (
        "Wheat_Upama",
        "ingredients",
        1,
    )
    assert parse_screenshot_path(Path("Wheat_Upama_ingredients_01.png")) is None
    assert slug_to_default_name("pumkin-aloo-tikki") == "Pumkin Aloo Tikki"

    draft = get_extractor("manual").extract("test-slug", [], [], "Custom Name")
    assert draft.name == "Custom Name"

    with tempfile.TemporaryDirectory() as tmp:
        incoming = Path(tmp) / "incoming"
        incoming.mkdir()
        ing1 = incoming / "demo__ingredients__01.png"
        ing2 = incoming / "demo__ingredients__02.png"
        inst = incoming / "demo__instructions.png"
        _make_screenshot(ing1, (200, 100, 50))
        _make_screenshot(ing2, (180, 90, 40))
        _make_screenshot(inst, (50, 100, 200))

        jobs = scan_incoming(incoming)
        assert "demo" in jobs
        assert len(jobs["demo"].ingredients) == 2
        assert jobs["demo"].is_ready()

        ensure_dirs()
        out_img = ROOT / "out" / "_smoke_demo.jpg"
        crop_hero_image(jobs["demo"].ingredients[0], out_img)
        assert out_img.is_file()
        out_img.unlink(missing_ok=True)

    print("smoke_test: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
