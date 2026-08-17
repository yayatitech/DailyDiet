"""Debug session logging (ops utility)."""

from __future__ import annotations

import json
import time
from pathlib import Path

SESSION_ID = "cea90e"
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "debug-cea90e.log"


def debug_log(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict | None = None,
    run_id: str = "pre-fix",
) -> None:
    # region agent log
    try:
        payload = {
            "sessionId": SESSION_ID,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass
    # endregion
