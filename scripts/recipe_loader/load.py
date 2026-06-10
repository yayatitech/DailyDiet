"""Push extracted recipes to DailyDiet admin API."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

import sys_path  # noqa: F401
from normalize import normalize_name_key
from paths import LOADER_ROOT, OUT
from state import StateStore


@dataclass
class LoadResult:
    status: str  # pushed | skipped_duplicate | failed
    name_key: str
    recipe_id: int | None = None
    message: str = ""


class CatalogClient:
    def __init__(self, base_url: str, admin_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-Admin-Key": admin_key}

    def list_recipes(self) -> list[dict]:
        with httpx.Client(timeout=60.0) as client:
            r = client.get(f"{self.base_url}/v1/recipes", headers=self.headers)
            r.raise_for_status()
            return r.json()

    def create_recipe(self, body: dict) -> dict:
        payload = {
            "name": body["name"],
            "display_name": body.get("display_name"),
            "ingredients": body.get("ingredients") or [],
            "instructions": body.get("instructions") or "",
            "external_url": body.get("external_url"),
        }
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                f"{self.base_url}/v1/admin/recipes",
                headers=self.headers,
                json=payload,
            )
            if r.status_code == 409:
                raise httpx.HTTPStatusError(
                    "duplicate",
                    request=r.request,
                    response=r,
                )
            r.raise_for_status()
            return r.json()

    def update_recipe(self, recipe_id: int, body: dict) -> dict:
        payload = {
            "name": body.get("name"),
            "display_name": body.get("display_name"),
            "ingredients": body.get("ingredients"),
            "instructions": body.get("instructions"),
            "external_url": body.get("external_url"),
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        with httpx.Client(timeout=60.0) as client:
            r = client.patch(
                f"{self.base_url}/v1/admin/recipes/{recipe_id}",
                headers=self.headers,
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    def upload_image(self, recipe_id: int, image_path: Path) -> dict:
        mime, _ = mimetypes.guess_type(str(image_path))
        if not mime:
            mime = "image/jpeg"
        with httpx.Client(timeout=120.0) as client:
            with image_path.open("rb") as f:
                r = client.post(
                    f"{self.base_url}/v1/admin/recipes/{recipe_id}/image",
                    headers=self.headers,
                    files={"file": (image_path.name, f, mime)},
                )
            r.raise_for_status()
            return r.json()


def push_recipe(
    client: CatalogClient,
    store: StateStore,
    payload: dict,
    image_path: Path | None,
    *,
    force_update: bool = False,
    dry_run: bool = False,
) -> LoadResult:
    name = str(payload["name"]).strip()
    name_key = normalize_name_key(name)

    exists, existing_id = store.catalog_has(name_key)
    if exists and not force_update:
        return LoadResult(
            status="skipped_duplicate",
            name_key=name_key,
            recipe_id=existing_id,
            message=f'catalog already has name_key "{name_key}" (id={existing_id})',
        )

    if dry_run:
        if exists and not force_update:
            return LoadResult(
                status="skipped_duplicate",
                name_key=name_key,
                recipe_id=existing_id,
                message=f'would skip duplicate "{name_key}"',
            )
        action = "would update" if exists and force_update else "would push"
        return LoadResult(
            status="pushed",
            name_key=name_key,
            recipe_id=existing_id,
            message=f"{action} {name!r}",
        )

    try:
        if exists and force_update and existing_id is not None:
            created = client.update_recipe(existing_id, payload)
            recipe_id = int(created["id"])
        else:
            created = client.create_recipe(payload)
            recipe_id = int(created["id"])
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 409:
            return LoadResult(
                status="skipped_duplicate",
                name_key=name_key,
                message="API returned 409 duplicate",
            )
        return LoadResult(
            status="failed",
            name_key=name_key,
            message=str(e),
        )
    except httpx.HTTPError as e:
        return LoadResult(
            status="failed",
            name_key=name_key,
            message=str(e),
        )

    if image_path and image_path.is_file():
        try:
            client.upload_image(recipe_id, image_path)
        except httpx.HTTPError as e:
            return LoadResult(
                status="failed",
                name_key=name_key,
                recipe_id=recipe_id,
                message=f"created id={recipe_id} but image upload failed: {e}",
            )

    store.set_catalog_from_api(client.list_recipes())
    return LoadResult(
        status="pushed",
        name_key=name_key,
        recipe_id=recipe_id,
        message=f"created id={recipe_id}" if not (exists and force_update) else f"updated id={recipe_id}",
    )


def load_json_file(
    path: Path,
    client: CatalogClient,
    store: StateStore,
    *,
    force_update: bool = False,
    dry_run: bool = False,
) -> LoadResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    slug = data.get("slug") or path.stem
    image_name = data.get("image_file") or f"{slug}.jpg"
    image_path = OUT / image_name
    if not image_path.is_file():
        image_path = path.parent / image_name
    return push_recipe(
        client,
        store,
        data,
        image_path if image_path.is_file() else None,
        force_update=force_update,
        dry_run=dry_run,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Load recipe JSON into catalog via admin API")
    parser.add_argument("json_files", nargs="+", help="Paths to out/*.json files")
    parser.add_argument("--force-update", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_url = os.environ.get("API_URL", "http://localhost:3000")
    admin_key = os.environ.get("ADMIN_KEY", os.environ.get("ADMIN_API_KEY", "")).strip()
    if not admin_key and not args.dry_run:
        print("ADMIN_KEY or ADMIN_API_KEY required", file=sys.stderr)
        return 1

    client = CatalogClient(api_url, admin_key)
    store = StateStore()
    if admin_key:
        try:
            store.set_catalog_from_api(client.list_recipes())
        except httpx.HTTPError as e:
            print(f"Warning: could not refresh catalog cache: {e}", file=sys.stderr)

    exit_code = 0
    for pattern in args.json_files:
        for path in sorted(Path(LOADER_ROOT).glob(pattern) if "*" in pattern else [Path(pattern)]):
            if not path.is_file():
                print(f"Skip missing: {path}")
                continue
            result = load_json_file(
                path,
                client,
                store,
                force_update=args.force_update,
                dry_run=args.dry_run,
            )
            slug = path.stem
            tag = result.status.upper()
            print(f"[{slug}] {tag} — {result.message}")
            if result.status == "failed":
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
