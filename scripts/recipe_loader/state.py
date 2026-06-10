"""Job state and catalog key cache on disk."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys_path  # noqa: F401

from normalize import normalize_name_key
from paths import CATALOG_KEYS_FILE, JOBS_FILE, STATE_DIR

JobStatus = str  # pushed | skipped_duplicate | failed | extracted


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def file_hashes(paths: list[Path]) -> list[str]:
    return [file_sha256(p) for p in sorted(paths, key=lambda p: p.name)]


class StateStore:
    def __init__(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._jobs = self._load_json(JOBS_FILE, default={})
        self._catalog_keys: dict[str, int] = self._load_json(CATALOG_KEYS_FILE, default={})

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.is_file():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default

    def _save_jobs(self) -> None:
        JOBS_FILE.write_text(json.dumps(self._jobs, indent=2), encoding="utf-8")

    def save_catalog_keys(self) -> None:
        CATALOG_KEYS_FILE.write_text(
            json.dumps(self._catalog_keys, indent=2),
            encoding="utf-8",
        )

    def set_catalog_from_api(self, recipes: list[dict]) -> None:
        self._catalog_keys = {}
        for row in recipes:
            name = str(row.get("name", "")).strip()
            rid = row.get("id")
            if name and rid is not None:
                self._catalog_keys[normalize_name_key(name)] = int(rid)
        self.save_catalog_keys()

    def catalog_has(self, name_key: str) -> tuple[bool, int | None]:
        rid = self._catalog_keys.get(name_key)
        return (rid is not None, rid)

    def catalog_size(self) -> int:
        return len(self._catalog_keys)

    def job_for_slug(self, slug: str) -> dict | None:
        return self._jobs.get(slug)

    def hashes_already_processed(self, hashes: list[str]) -> bool:
        hash_set = set(hashes)
        for job in self._jobs.values():
            if job.get("status") not in ("pushed", "skipped_duplicate"):
                continue
            stored = set(job.get("file_hashes") or [])
            if hash_set and hash_set <= stored:
                return True
        return False

    def name_key_pushed_locally(self, name_key: str) -> bool:
        for job in self._jobs.values():
            if job.get("status") == "pushed" and job.get("name_key") == name_key:
                return True
        return False

    def record_job(
        self,
        slug: str,
        *,
        status: JobStatus,
        name_key: str | None = None,
        recipe_id: int | None = None,
        file_hashes: list[str] | None = None,
        error: str | None = None,
        extractor: str | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "status": status,
            "updated_at": _utc_now(),
        }
        if name_key is not None:
            entry["name_key"] = name_key
        if recipe_id is not None:
            entry["recipe_id"] = recipe_id
        if file_hashes is not None:
            entry["file_hashes"] = file_hashes
        if error:
            entry["error"] = error
        if extractor:
            entry["extractor"] = extractor
        if status == "pushed":
            entry["pushed_at"] = _utc_now()

        prev = self._jobs.get(slug) or {}
        self._jobs[slug] = {**prev, **entry}
        self._save_jobs()

        if status == "pushed" and name_key and recipe_id is not None:
            self._catalog_keys[name_key] = recipe_id
            self.save_catalog_keys()
