"""Paths for the recipe_loader ops utility."""

from __future__ import annotations

from pathlib import Path

LOADER_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = LOADER_ROOT.parent.parent

INCOMING = LOADER_ROOT / "in" / "incoming"
PROCESSING = LOADER_ROOT / "in" / "processing"
DONE = LOADER_ROOT / "in" / "done"
SKIPPED_DUPLICATE = LOADER_ROOT / "in" / "skipped" / "duplicate"
FAILED = LOADER_ROOT / "in" / "failed"
OUT = LOADER_ROOT / "out"
STATE_DIR = LOADER_ROOT / "state"
JOBS_FILE = STATE_DIR / "jobs.json"
CATALOG_KEYS_FILE = STATE_DIR / "catalog_keys.json"


def ensure_dirs() -> None:
    for path in (
        INCOMING,
        PROCESSING,
        DONE,
        SKIPPED_DUPLICATE,
        FAILED,
        OUT,
        STATE_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
