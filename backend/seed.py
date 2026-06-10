"""Seed PostgreSQL from public/data/meal-plan.json."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "public" / "data" / "meal-plan.json"
CATALOG_PATH = ROOT / "public" / "data" / "recipe-catalog.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal, engine, Base  # noqa: E402
from app.deps import parse_start_date  # noqa: E402
from app.meals import normalize_meal_name  # noqa: E402
from app.models import (
    DAY_KEYS,
    MealCompletion,
    PlanTemplate,
    RecipeCatalogEntry,
    TemplateMeal,
    TemplateWeek,
    TimeSlot,
    UserMealOverride,
    UserWeekNotes,
)  # noqa: E402


def seed_recipe_catalog(db: Session) -> None:
    if not CATALOG_PATH.exists():
        print(f"No recipe catalog at {CATALOG_PATH}, skipping")
        return
    entries = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    db.query(RecipeCatalogEntry).delete()
    count = 0
    for item in entries:
        name = item.get("name", "").strip()
        if not name:
            continue
        external_url = (item.get("external_url") or item.get("recipe_url") or "").strip() or None
        display_name = (item.get("display_name") or "").strip() or None
        ingredients = item.get("ingredients") or []
        instructions = (item.get("instructions") or "").strip()
        if not external_url and not ingredients and not instructions:
            continue
        db.add(
            RecipeCatalogEntry(
                name=name,
                name_key=normalize_meal_name(name),
                display_name=display_name,
                ingredients=ingredients,
                instructions=instructions,
                external_url=external_url,
            )
        )
        count += 1
    db.commit()
    print(f"Seeded {count} recipe catalog entries from {CATALOG_PATH}")


def run_seed(db: Session | None = None) -> None:
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Missing {JSON_PATH}")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    own_session = db is None
    if own_session:
        db = SessionLocal()

    assert db is not None

    db.query(MealCompletion).delete()
    db.query(UserMealOverride).delete()
    db.query(UserWeekNotes).delete()
    db.query(TemplateMeal).delete()
    db.query(TemplateWeek).delete()
    db.query(PlanTemplate).delete()
    db.query(TimeSlot).delete()
    db.commit()

    for slot in data.get("timeSlots", []):
        db.add(
            TimeSlot(
                id=slot["id"],
                slot_index=slot["id"] - 1,
                label=slot["label"],
                time_label=slot["time"],
            )
        )

    template = PlanTemplate(name="Weekly Meal Plan", source=str(JSON_PATH.name))
    db.add(template)
    db.flush()

    for idx, week in enumerate(data.get("weeks", []), start=1):
        start = parse_start_date(week.get("title", ""))
        tw = TemplateWeek(
            template_id=template.id,
            week_key=week["id"],
            week_index=idx,
            title=week["title"],
            start_date=start,
            notes=week.get("notes", ""),
        )
        db.add(tw)
        db.flush()
        meals = week.get("meals", {})
        for day_idx, day_key in enumerate(DAY_KEYS):
            for slot_idx, content in enumerate(meals.get(day_key, [])[:8]):
                db.add(
                    TemplateMeal(
                        week_id=tw.id,
                        day_of_week=day_idx,
                        slot_index=slot_idx,
                        content=content or "",
                    )
                )

    db.commit()
    if own_session:
        db.close()
    print(f"Seeded {len(data.get('weeks', []))} weeks from {JSON_PATH}")


def run_full_seed(db: Session | None = None) -> None:
    run_seed(db)
    own_session = db is None
    if own_session:
        db = SessionLocal()
    assert db is not None
    seed_recipe_catalog(db)
    if own_session:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    run_full_seed()
