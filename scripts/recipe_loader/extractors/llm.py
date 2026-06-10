"""OpenAI vision extraction."""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

import sys_path  # noqa: F401

from normalize import slug_to_default_name

from .base import RecipeDraft

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


def _encode_image(path: Path) -> str:
    data = path.read_bytes()
    ext = path.suffix.lower()
    mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png" if ext == ".png" else "image/webp"
    return f"data:{mime};base64,{base64.standard_b64encode(data).decode('ascii')}"


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_BLOCK.search(text)
        if not match:
            raise
        return json.loads(match.group(0))


class LlmExtractor:
    def extract(
        self,
        slug: str,
        ingredients_path: Path,
        instructions_path: Path | None,
        name_override: str | None,
    ) -> RecipeDraft:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for --extractor llm")

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")

        default_name = name_override or slug_to_default_name(slug)
        content: list[dict] = [
            {
                "type": "text",
                "text": (
                    "Extract recipe data from these mobile app screenshots. "
                    f'Default catalog name (meal plan spelling): "{default_name}". '
                    "Return ONLY valid JSON with keys: name, display_name, ingredients, instructions.\n"
                    "- name: string, use default unless screenshot title differs\n"
                    "- display_name: string or null\n"
                    "- ingredients: array of {amount, item} from the ingredients list\n"
                    "- instructions: string, full step text from instructions screen; empty if missing\n"
                ),
            },
            {"type": "image_url", "image_url": {"url": _encode_image(ingredients_path)}},
        ]
        if instructions_path and instructions_path.is_file():
            content.append(
                {"type": "image_url", "image_url": {"url": _encode_image(instructions_path)}}
            )

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=4096,
        )
        raw = response.choices[0].message.content or ""
        data = _parse_json_response(raw)

        ingredients = []
        for item in data.get("ingredients") or []:
            if not isinstance(item, dict):
                continue
            ing_item = str(item.get("item", "")).strip()
            if not ing_item:
                continue
            ingredients.append(
                {"amount": str(item.get("amount", "")).strip(), "item": ing_item}
            )

        name = str(data.get("name") or default_name).strip() or default_name
        display = data.get("display_name")
        display_name = str(display).strip() if display else name

        return RecipeDraft(
            name=name,
            display_name=display_name,
            ingredients=ingredients,
            instructions=str(data.get("instructions") or "").strip(),
            extractor="llm",
        )
