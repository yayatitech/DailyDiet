import re
from datetime import date
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import user_id_from_token
from app.config import settings
from app.database import get_db
from app.meals import enrich_items, join_slot_content
from app.models import DAY_KEYS, MealCompletion, RecipeCatalogEntry, TemplateWeek, User, UserMealOverride, UserWeekNotes
from app.recipe_utils import recipe_lookup_from_entry
from app.schemas import MealItemOut, WeekDetail

security = HTTPBearer(auto_error=False)


def day_to_index(day: str) -> int:
    try:
        return DAY_KEYS.index(day)  # type: ignore[arg-type]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid day: {day}") from e


def index_to_day(index: int) -> str:
    return DAY_KEYS[index]


def parse_start_date(title: str) -> date | None:
    m = re.search(r"starting:\s*(.+)$", title, re.I)
    if not m or not m.group(1).strip():
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            from datetime import datetime

            return datetime.strptime(m.group(1).strip(), fmt).date()
        except ValueError:
            continue
    return None


def get_or_create_dev_user(db: Session) -> User:
    user = db.query(User).filter(User.email == settings.default_dev_email).first()
    if user:
        return user
    from app.auth import hash_password

    user = User(email=settings.default_dev_email, password_hash=hash_password(settings.default_dev_password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if credentials:
        user_id = user_id_from_token(credentials.credentials, "access")
        if user_id:
            user = db.get(User, user_id)
            if user:
                return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return get_or_create_dev_user(db)


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin key required")


def get_week_by_key(db: Session, week_key: str) -> TemplateWeek:
    week = db.query(TemplateWeek).filter(TemplateWeek.week_key == week_key).first()
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")
    return week


def get_recipe_catalog_map(db: Session):
    rows = db.query(RecipeCatalogEntry).all()
    return {entry.name_key: recipe_lookup_from_entry(entry) for entry in rows}


def build_week_detail(db: Session, week: TemplateWeek, user: User) -> WeekDetail:
    catalog = get_recipe_catalog_map(db)
    template_meals = {
        (m.day_of_week, m.slot_index): m.content for m in week.meals
    }
    overrides = {
        (o.day_of_week, o.slot_index): o.content
        for o in db.query(UserMealOverride)
        .filter(UserMealOverride.user_id == user.id, UserMealOverride.week_id == week.id)
        .all()
    }
    notes_row = (
        db.query(UserWeekNotes)
        .filter(UserWeekNotes.user_id == user.id, UserWeekNotes.week_id == week.id)
        .first()
    )
    notes = notes_row.notes if notes_row else week.notes

    meals: dict[str, list[list[MealItemOut]]] = {}
    for day_idx, day_key in enumerate(DAY_KEYS):
        row: list[list[MealItemOut]] = []
        for slot in range(8):
            content = overrides.get((day_idx, slot), template_meals.get((day_idx, slot), ""))
            row.append(enrich_items(content, catalog))
        meals[day_key] = row

    return WeekDetail(
        id=week.week_key,
        title=week.title,
        start_date=week.start_date,
        notes=notes,
        meals=meals,
    )


def week_detail_to_export_meals(detail: WeekDetail) -> dict[str, list[str]]:
    """Flatten enriched meal items to newline strings for JSON backup."""
    exported: dict[str, list[str]] = {}
    for day_key, slots in detail.meals.items():
        exported[day_key] = [join_slot_content(slot) for slot in slots]
    return exported


def slot_content_from_import(value: str | list) -> str:
    """Accept legacy string or enriched item list from older exports."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        if not value:
            return ""
        if isinstance(value[0], dict):
            return "\n".join(str(item.get("text", "")).strip() for item in value if item.get("text"))
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return str(value)
