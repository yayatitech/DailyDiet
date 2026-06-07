#!/usr/bin/env python3
"""CLI: extract recipe from screenshot pair without folder watch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import sys_path  # noqa: F401
from crop import crop_hero_image
from extractors import get_extractor
from paths import OUT, ensure_dirs
from pairing import RecipeFiles


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract recipe JSON from screenshots")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--ingredients", required=True, type=str)
    parser.add_argument("--instructions", type=str, default="")
    parser.add_argument("--extractor", default=None, choices=["llm", "ocr", "manual"])
    parser.add_argument("--name", default=None, help="Override catalog name")
    args = parser.parse_args()

    ensure_dirs()
    ingredients = Path(args.ingredients)
    instructions = Path(args.instructions) if args.instructions else None

    if not ingredients.is_file():
        print(f"Missing ingredients file: {ingredients}", file=sys.stderr)
        return 1

    extractor = get_extractor(args.extractor)
    draft = extractor.extract(args.slug, ingredients, instructions, args.name)

    image_file = f"{args.slug}.jpg"
    image_path = OUT / image_file
    crop_hero_image(ingredients, image_path)

    sources = [ingredients.name]
    if instructions:
        sources.append(instructions.name)
    payload = draft.to_payload(args.slug, image_file, sources)
    out_json = OUT / f"{args.slug}.json"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_json} and {image_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
