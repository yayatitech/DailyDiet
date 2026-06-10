#!/usr/bin/env python3
"""Watch incoming folder for recipe screenshots and process them."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import httpx

import sys_path  # noqa: F401
from load import CatalogClient
from pairing import scan_incoming
from paths import INCOMING, ensure_dirs
from pipeline import run_job
from state import StateStore


class DebouncedWatcher:
    def __init__(
        self,
        watch_dir: Path,
        debounce_ms: int,
        on_tick,
    ) -> None:
        self.watch_dir = watch_dir
        self.debounce_s = debounce_ms / 1000.0
        self.on_tick = on_tick
        self._pending: dict[str, float] = {}

    def notify(self, path: Path) -> None:
        if path.parent.resolve() != self.watch_dir.resolve():
            return
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            return
        self._pending[str(path.resolve())] = time.monotonic()

    def flush_ready(self) -> None:
        now = time.monotonic()
        ready = [
            p
            for p, t in list(self._pending.items())
            if now - t >= self.debounce_s
        ]
        for p in ready:
            del self._pending[p]
        if ready:
            self.on_tick()

    def run_poll(self, interval_s: float = 2.0) -> None:
        seen: set[str] = set()
        while True:
            for path in self.watch_dir.iterdir():
                if not path.is_file():
                    continue
                key = str(path.resolve())
                mtime = path.stat().st_mtime
                token = f"{key}:{mtime}"
                if token not in seen:
                    seen.add(token)
                    self.notify(path)
            self.flush_ready()
            time.sleep(interval_s)


def process_all_pending(
    incoming_dir: Path,
    *,
    extractor: str,
    store: StateStore,
    client: CatalogClient | None,
    no_push: bool,
    dry_run: bool,
    force_update: bool,
    allow_partial: bool,
    pair_timeout: float,
    pending_since: dict[str, float],
) -> None:
    jobs = scan_incoming(incoming_dir)
    now = time.monotonic()
    for slug in sorted(jobs):
        job = jobs[slug]
        partial = allow_partial
        if job.ingredients and not job.instructions:
            if slug not in pending_since:
                pending_since[slug] = now
            elapsed = now - pending_since[slug]
            if elapsed < pair_timeout:
                continue
            partial = True
        else:
            pending_since.pop(slug, None)

        msg = run_job(
            job,
            extractor_name=extractor,
            store=store,
            client=client,
            incoming_dir=incoming_dir,
            no_push=no_push,
            dry_run=dry_run,
            force_update=force_update,
            allow_partial=partial,
        )
        print(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch folder for recipe screenshots")
    parser.add_argument("--watch-dir", type=Path, default=INCOMING)
    parser.add_argument("--extractor", default=None, choices=["llm", "ocr", "manual"])
    parser.add_argument("--debounce-ms", type=int, default=2000)
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--review", action="store_true", help="Same as --no-push")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--force-update", action="store_true")
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--pair-timeout", type=float, default=120.0)
    args = parser.parse_args()

    no_push = args.no_push or args.review
    ensure_dirs()
    watch_dir = args.watch_dir.resolve()
    watch_dir.mkdir(parents=True, exist_ok=True)

    extractor = args.extractor or os.environ.get("RECIPE_EXTRACTOR", "llm")
    api_url = os.environ.get("API_URL", "http://localhost:3000")
    admin_key = os.environ.get("ADMIN_KEY", os.environ.get("ADMIN_API_KEY", "")).strip()

    store = StateStore()
    client: CatalogClient | None = None
    if not no_push and not args.dry_run:
        if not admin_key:
            print("ADMIN_KEY or ADMIN_API_KEY required for push", file=sys.stderr)
            return 1
        client = CatalogClient(api_url, admin_key)
        try:
            store.set_catalog_from_api(client.list_recipes())
            print(f"Catalog cache: {store.catalog_size()} recipes")
        except httpx.HTTPError as e:
            print(f"Warning: could not refresh catalog: {e}", file=sys.stderr)
    elif admin_key:
        client = CatalogClient(api_url, admin_key)

    pending_since: dict[str, float] = {}

    def tick() -> None:
        process_all_pending(
            watch_dir,
            extractor=extractor,
            store=store,
            client=client,
            no_push=no_push,
            dry_run=args.dry_run,
            force_update=args.force_update,
            allow_partial=args.allow_partial,
            pair_timeout=args.pair_timeout,
            pending_since=pending_since,
        )

    print(f"Watching {watch_dir} (extractor={extractor}, no_push={no_push})")

    if args.poll:
        watcher = DebouncedWatcher(watch_dir, args.debounce_ms, tick)
        try:
            watcher.run_poll(args.poll_interval)
        except KeyboardInterrupt:
            print("\nStopped.")
        return 0

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("watchdog not installed; use --poll", file=sys.stderr)
        return 1

    watcher = DebouncedWatcher(watch_dir, args.debounce_ms, tick)

    class Handler(FileSystemEventHandler):
        def on_created(self, event):  # noqa: ANN001
            if not event.is_directory:
                watcher.notify(Path(event.src_path))

        def on_modified(self, event):  # noqa: ANN001
            if not event.is_directory:
                watcher.notify(Path(event.src_path))

    observer = Observer()
    observer.schedule(Handler(), str(watch_dir), recursive=False)
    observer.start()
    try:
        while True:
            watcher.flush_ready()
            time.sleep(0.3)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped.")
    observer.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
