#!/usr/bin/env python3
"""Import weekly meal plan from .xlsm to public/data/meal-plan.json."""

from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XLSM_PATH = ROOT / "simple_weekly_meal_plan_extendable.xlsm"
OUT_PATH = ROOT / "public" / "data" / "meal-plan.json"

DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_COLS = ["B", "C", "D", "E", "F", "G", "H"]

WEEK_HEADER_RE = re.compile(r"^Week\s+(\d+)\s+starting:\s*(.*)$", re.IGNORECASE)
MEAL_LABEL_RE = re.compile(
    r"Meal\s*(\d+)\s*(?:[/\n]\s*)?([\d:]+\s*(?:AM|PM)?)?",
    re.IGNORECASE,
)
CELL_REF_RE = re.compile(r"^([A-Z]+)(\d+)$")

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

AUTO_DATE_UNTIL_WEEK = 10

DEFAULT_TIME_SLOTS = [
    {"id": 1, "label": "Meal 1", "time": "6:30 AM"},
    {"id": 2, "label": "Meal 2", "time": "8:00 AM"},
    {"id": 3, "label": "Meal 3", "time": "10:00 AM"},
    {"id": 4, "label": "Meal 4", "time": "1:00 PM"},
    {"id": 5, "label": "Meal 5", "time": "3:00 PM"},
    {"id": 6, "label": "Meal 6", "time": "6:00 PM"},
    {"id": 7, "label": "Meal 7", "time": "8:00 PM"},
    {"id": 8, "label": "Meal 8", "time": "10:00 PM"},
]


class SheetReader:
    def __init__(self, path: Path) -> None:
        self.cells: dict[str, str] = {}
        self.max_row = 1
        with zipfile.ZipFile(path) as zf:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in zf.namelist():
                root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                for si in root.findall(".//m:si", NS):
                    texts = [t.text or "" for t in si.findall(".//m:t", NS)]
                    shared.append("".join(texts))

            sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            for c in sheet.findall(".//m:c", NS):
                ref = c.get("r")
                if not ref:
                    continue
                m = CELL_REF_RE.match(ref)
                if not m:
                    continue
                row = int(m.group(2))
                self.max_row = max(self.max_row, row)
                v = c.find("m:v", NS)
                if v is None or v.text is None:
                    continue
                val = v.text
                if c.get("t") == "s":
                    val = shared[int(val)]
                self.cells[ref] = str(val).strip()

    def get(self, col: str, row: int) -> str:
        return self.cells.get(f"{col}{row}", "")


def normalize_time(raw: str) -> str:
    if not raw:
        return ""
    t = raw.strip().upper()
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?$", t.replace(" ", ""))
    if not m:
        return raw.strip()
    hour = int(m.group(1))
    minute = m.group(2) or "00"
    ampm = m.group(3) or ""
    if ampm:
        return f"{hour}:{minute} {ampm}"
    guess = {1: "PM", 3: "PM", 6: "PM", 8: "PM", 10: "PM"}.get(hour, "AM")
    if hour == 6 and int(minute) == 30:
        guess = "AM"
    if hour == 8 and minute == "00":
        guess = "AM"
    if hour == 10:
        guess = "AM"
    return f"{hour}:{minute} {guess}"


def parse_meal_label(label: str) -> tuple[int | None, str]:
    if not label:
        return None, ""
    m = MEAL_LABEL_RE.search(label.replace("\r\n", "\n"))
    if not m:
        return None, ""
    return int(m.group(1)), normalize_time(m.group(2) or "")


def empty_week_meals() -> dict[str, list[str]]:
    return {day: [""] * 8 for day in DAY_KEYS}


def find_week_blocks(ws: SheetReader) -> list[tuple[int, str, int]]:
    blocks: list[tuple[int, str, int]] = []
    for row in range(1, ws.max_row + 1):
        val = ws.get("A", row)
        m = WEEK_HEADER_RE.match(val)
        if m:
            week_num = int(m.group(1))
            date_part = m.group(2).strip()
            title = val
            if date_part:
                title = f"Week {week_num} starting: {date_part}"
            blocks.append((week_num, title, row))
    return blocks


def read_week_block(ws: SheetReader, header_row: int, week_index: int, title: str) -> dict:
    meals = empty_week_meals()
    time_slots_from_sheet: dict[int, str] = {}

    meal_start = header_row + 2
    for offset in range(8):
        row = meal_start + offset
        label = ws.get("A", row)
        slot_id, time_part = parse_meal_label(label)
        if slot_id is not None and time_part:
            time_slots_from_sheet[slot_id] = time_part

        for col, day in zip(DAY_COLS, DAY_KEYS):
            meals[day][offset] = ws.get(col, row)

    notes_row = meal_start + 8
    notes = ""
    if ws.get("A", notes_row).lower().startswith("notes"):
        notes = ws.get("B", notes_row)

    return {
        "id": f"week-{week_index}",
        "title": title,
        "meals": meals,
        "notes": notes,
        "_time_overrides": time_slots_from_sheet,
    }


def format_start_date(d: datetime) -> str:
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def parse_start_date(date_str: str) -> datetime | None:
    date_str = date_str.strip()
    if not date_str:
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def title_start_date(title: str) -> datetime | None:
    m = re.search(r"starting:\s*(.+)$", title, re.IGNORECASE)
    if not m:
        return None
    return parse_start_date(m.group(1))


def resolve_week_title(
    week_num: int,
    week_index: int,
    title: str,
    last_date: datetime | None,
) -> tuple[str, datetime | None]:
    current = title_start_date(title)
    if current is not None:
        return title, current
    if last_date is None or week_index > AUTO_DATE_UNTIL_WEEK:
        return title, last_date
    next_date = last_date + timedelta(days=7)
    return f"Week {week_num} starting: {format_start_date(next_date)}", next_date


def build_time_slots(all_overrides: list[dict[int, str]]) -> list[dict]:
    slots = [dict(s) for s in DEFAULT_TIME_SLOTS]
    for overrides in all_overrides:
        for slot_id, time_str in overrides.items():
            if 1 <= slot_id <= 8 and time_str:
                slots[slot_id - 1]["time"] = time_str
    return slots


def main() -> None:
    if not XLSM_PATH.exists():
        raise SystemExit(f"Missing workbook: {XLSM_PATH}")

    ws = SheetReader(XLSM_PATH)
    blocks = find_week_blocks(ws)
    weeks: list[dict] = []
    all_overrides: list[dict[int, str]] = []

    last_date: datetime | None = None
    for idx, (sheet_week_num, title, header_row) in enumerate(blocks, start=1):
        title, last_date = resolve_week_title(sheet_week_num, idx, title, last_date)
        week = read_week_block(ws, header_row, idx, title)
        all_overrides.append(week.pop("_time_overrides"))
        weeks.append(week)

    plan = {
        "timeSlots": build_time_slots(all_overrides),
        "weeks": weeks,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(weeks)} weeks to {OUT_PATH}")


if __name__ == "__main__":
    main()
