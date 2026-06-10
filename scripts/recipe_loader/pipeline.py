"""Run a single recipe job: extract, dedupe, push, archive."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import sys_path  # noqa: F401
from crop import crop_hero_image
from extractors import get_extractor
from load import CatalogClient, LoadResult, push_recipe
from normalize import normalize_name_key
from pairing import RecipeFiles, read_name_override
from paths import DONE, FAILED, OUT, SKIPPED_DUPLICATE
from state import StateStore, file_hashes


def _archive(slug: str, files: RecipeFiles, dest_root: Path) -> None:
    dest = dest_root / slug
    dest.mkdir(parents=True, exist_ok=True)
    for path in (files.ingredients, files.instructions):
        if path and path.is_file():
            shutil.move(str(path), str(dest / path.name))


def _write_error(slug: str, message: str, dest_root: Path = FAILED) -> None:
    dest = dest_root / slug
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "error.log").write_text(message, encoding="utf-8")


def run_job(
    job: RecipeFiles,
    *,
    extractor_name: str,
    store: StateStore,
    client: CatalogClient | None,
    incoming_dir: Path,
    no_push: bool = False,
    dry_run: bool = False,
    force_update: bool = False,
    allow_partial: bool = False,
) -> str:
    """
    Process one recipe job. Returns status string for logging.
    """
    slug = job.slug
    prefix = f"[{slug}]"

    if job.ingredients is None:
        return f"{prefix} SKIP — missing ingredients file"

    paths_for_hash = [p for p in (job.ingredients, job.instructions) if p]
    hashes = file_hashes(paths_for_hash)

    if store.hashes_already_processed(hashes):
        _archive(slug, job, SKIPPED_DUPLICATE)
        store.record_job(slug, status="skipped_duplicate", file_hashes=hashes)
        return f"{prefix} SKIP duplicate — same files already processed"

    if not job.is_ready(allow_partial=allow_partial):
        return f"{prefix} WAIT — need __instructions screenshot"

    name_override = read_name_override(incoming_dir, slug)
    extractor = get_extractor(extractor_name)
    draft = extractor.extract(slug, job.ingredients, job.instructions, name_override)

    image_file = f"{slug}.jpg"
    image_path = OUT / image_file
    crop_hero_image(job.ingredients, image_path)

    sources = [p.name for p in paths_for_hash]
    payload = draft.to_payload(slug, image_file, sources)
    json_path = OUT / f"{slug}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    name_key = normalize_name_key(draft.name)
    exists, existing_id = store.catalog_has(name_key)
    if store.name_key_pushed_locally(name_key) and not force_update:
        exists = True

    if exists and not force_update:
        _archive(slug, job, SKIPPED_DUPLICATE)
        store.record_job(
            slug,
            status="skipped_duplicate",
            name_key=name_key,
            recipe_id=existing_id,
            file_hashes=hashes,
            extractor=draft.extractor,
        )
        return (
            f'{prefix} SKIP duplicate — catalog already has name_key "{name_key}"'
            f"{f' (id={existing_id})' if existing_id else ''}"
        )

    if no_push:
        store.record_job(
            slug,
            status="extracted",
            name_key=name_key,
            file_hashes=hashes,
            extractor=draft.extractor,
        )
        return f"{prefix} EXTRACT ok — wrote {json_path.name} (--no-push)"

    if client is None:
        return f"{prefix} FAIL — ADMIN_KEY required for push"

    result: LoadResult = push_recipe(
        client,
        store,
        payload,
        image_path,
        force_update=force_update,
        dry_run=dry_run,
    )

    if result.status == "skipped_duplicate":
        _archive(slug, job, SKIPPED_DUPLICATE)
        store.record_job(
            slug,
            status="skipped_duplicate",
            name_key=name_key,
            recipe_id=result.recipe_id,
            file_hashes=hashes,
            extractor=draft.extractor,
        )
        return f"{prefix} SKIP duplicate — {result.message}"

    if result.status == "failed":
        _archive(slug, job, FAILED)
        _write_error(slug, result.message)
        store.record_job(
            slug,
            status="failed",
            name_key=name_key,
            file_hashes=hashes,
            error=result.message,
            extractor=draft.extractor,
        )
        return f"{prefix} FAIL — {result.message}"

    _archive(slug, job, DONE)
    store.record_job(
        slug,
        status="pushed",
        name_key=name_key,
        recipe_id=result.recipe_id,
        file_hashes=hashes,
        extractor=draft.extractor,
    )
    return f"{prefix} PUSH ok — {result.message}"
