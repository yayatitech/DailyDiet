"""Crop hero dish photo from the top of an ingredients screenshot."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def crop_hero_image(source: Path, dest: Path, *, top_fraction: float = 0.4) -> None:
    """Save the top portion of the screenshot as the recipe hero image."""
    with Image.open(source) as img:
        rgb = img.convert("RGB")
        width, height = rgb.size
        crop_h = max(1, int(height * top_fraction))
        cropped = rgb.crop((0, 0, width, crop_h))
        dest.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(dest, format="JPEG", quality=90)
