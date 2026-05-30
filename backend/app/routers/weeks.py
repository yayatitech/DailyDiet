from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import build_week_detail, day_to_index, get_current_user, get_week_by_key, index_to_day, require_admin
from app.models import (
    DAY_KEYS,
    MealCompletion,
    TemplateWeek,
    TimeSlot,
    User,
    UserMealOverride,
    UserWeekNotes,
)
from app.schemas import (
    CompletionOut,
    CompletionToggle,
    ExportBundle,
    MealPatch,
    NotesPatch,
    TimeSlotOut,
    UserOut,
    WeekDetail,
    WeekSummary,
)

router = APIRouter(prefix="/v1", tags=["weeks"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/time-slots", response_model=list[TimeSlotOut])
def list_time_slots(db: Session = Depends(get_db)):
    slots = db.query(TimeSlot).order_by(TimeSlot.slot_index).all()
    return [TimeSlotOut(id=s.id, label=s.label, time=s.time_label) for s in slots]


@router.get("/weeks", response_model=list[WeekSummary])
def list_weeks(db: Session = Depends(get_db)):
    weeks = db.query(TemplateWeek).order_by(TemplateWeek.week_index).all()
    return [
        WeekSummary(id=w.week_key, title=w.title, start_date=w.start_date) for w in weeks
    ]


@router.get("/weeks/{week_key}", response_model=WeekDetail)
def get_week(week_key: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    week = get_week_by_key(db, week_key)
    return build_week_detail(db, week, user)


@router.patch("/weeks/{week_key}/meals")
def patch_meal(
    week_key: str,
    body: MealPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    week = get_week_by_key(db, week_key)
    day_idx = day_to_index(body.day)
    row = (
        db.query(UserMealOverride)
        .filter(
            UserMealOverride.user_id == user.id,
            UserMealOverride.week_id == week.id,
            UserMealOverride.day_of_week == day_idx,
            UserMealOverride.slot_index == body.slot_index,
        )
        .first()
    )
    if row:
        row.content = body.content
    else:
        db.add(
            UserMealOverride(
                user_id=user.id,
                week_id=week.id,
                day_of_week=day_idx,
                slot_index=body.slot_index,
                content=body.content,
            )
        )
    db.commit()
    return {"ok": True}


@router.patch("/weeks/{week_key}/notes")
def patch_notes(
    week_key: str,
    body: NotesPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    week = get_week_by_key(db, week_key)
    row = (
        db.query(UserWeekNotes)
        .filter(UserWeekNotes.user_id == user.id, UserWeekNotes.week_id == week.id)
        .first()
    )
    if row:
        row.notes = body.notes
    else:
        db.add(UserWeekNotes(user_id=user.id, week_id=week.id, notes=body.notes))
    db.commit()
    return {"ok": True}


@router.post("/weeks/{week_key}/reset")
def reset_week(
    week_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    week = get_week_by_key(db, week_key)
    db.query(UserMealOverride).filter(
        UserMealOverride.user_id == user.id, UserMealOverride.week_id == week.id
    ).delete()
    db.query(UserWeekNotes).filter(
        UserWeekNotes.user_id == user.id, UserWeekNotes.week_id == week.id
    ).delete()
    db.commit()
    return {"ok": True}


@router.get("/weeks/{week_key}/completions", response_model=list[CompletionOut])
def list_completions(
    week_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    week = get_week_by_key(db, week_key)
    rows = (
        db.query(MealCompletion)
        .filter(MealCompletion.user_id == user.id, MealCompletion.week_id == week.id)
        .all()
    )
    return [
        CompletionOut(day=index_to_day(r.day_of_week), slot_index=r.slot_index, completed=True)
        for r in rows
    ]


@router.put("/weeks/{week_key}/completions")
def toggle_completion(
    week_key: str,
    body: CompletionToggle,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    week = get_week_by_key(db, week_key)
    day_idx = day_to_index(body.day)
    row = (
        db.query(MealCompletion)
        .filter(
            MealCompletion.user_id == user.id,
            MealCompletion.week_id == week.id,
            MealCompletion.day_of_week == day_idx,
            MealCompletion.slot_index == body.slot_index,
        )
        .first()
    )
    if body.completed:
        if not row:
            db.add(
                MealCompletion(
                    user_id=user.id,
                    week_id=week.id,
                    day_of_week=day_idx,
                    slot_index=body.slot_index,
                )
            )
    elif row:
        db.delete(row)
    db.commit()
    return {"ok": True}


@router.delete("/completions")
def clear_completions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(MealCompletion).filter(MealCompletion.user_id == user.id).delete()
    db.commit()
    return {"ok": True}


@router.get("/export", response_model=ExportBundle)
def export_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    weeks = db.query(TemplateWeek).order_by(TemplateWeek.week_index).all()
    slots = db.query(TimeSlot).order_by(TimeSlot.slot_index).all()
    plan_weeks = [build_week_detail(db, w, user).model_dump() for w in weeks]
    tracking: dict[str, bool] = {}
    for c in db.query(MealCompletion).filter(MealCompletion.user_id == user.id).all():
        week = db.get(TemplateWeek, c.week_id)
        if week:
            key = f"{week.week_key}:{index_to_day(c.day_of_week)}:{c.slot_index}"
            tracking[key] = True
    return ExportBundle(
        plan={
            "timeSlots": [{"id": s.id, "label": s.label, "time": s.time_label} for s in slots],
            "weeks": plan_weeks,
        },
        tracking=tracking,
        exported_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/import")
def import_data(
    bundle: ExportBundle,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for week_data in bundle.plan.get("weeks", []):
        week_key = week_data.get("id")
        if not week_key:
            continue
        week = get_week_by_key(db, week_key)
        meals = week_data.get("meals", {})
        for day_key, slots in meals.items():
            day_idx = day_to_index(day_key)
            for slot_idx, content in enumerate(slots[:8]):
                template = next(
                    (m for m in week.meals if m.day_of_week == day_idx and m.slot_index == slot_idx),
                    None,
                )
                template_content = template.content if template else ""
                if content == template_content:
                    db.query(UserMealOverride).filter(
                        UserMealOverride.user_id == user.id,
                        UserMealOverride.week_id == week.id,
                        UserMealOverride.day_of_week == day_idx,
                        UserMealOverride.slot_index == slot_idx,
                    ).delete()
                else:
                    row = (
                        db.query(UserMealOverride)
                        .filter(
                            UserMealOverride.user_id == user.id,
                            UserMealOverride.week_id == week.id,
                            UserMealOverride.day_of_week == day_idx,
                            UserMealOverride.slot_index == slot_idx,
                        )
                        .first()
                    )
                    if row:
                        row.content = content
                    else:
                        db.add(
                            UserMealOverride(
                                user_id=user.id,
                                week_id=week.id,
                                day_of_week=day_idx,
                                slot_index=slot_idx,
                                content=content,
                            )
                        )
        notes = week_data.get("notes", "")
        if notes != week.notes:
            row = (
                db.query(UserWeekNotes)
                .filter(UserWeekNotes.user_id == user.id, UserWeekNotes.week_id == week.id)
                .first()
            )
            if row:
                row.notes = notes
            else:
                db.add(UserWeekNotes(user_id=user.id, week_id=week.id, notes=notes))
        else:
            db.query(UserWeekNotes).filter(
                UserWeekNotes.user_id == user.id, UserWeekNotes.week_id == week.id
            ).delete()

    db.query(MealCompletion).filter(MealCompletion.user_id == user.id).delete()
    for cell_id, done in bundle.tracking.items():
        if not done:
            continue
        parts = cell_id.split(":")
        if len(parts) != 3:
            continue
        wk, day, slot_s = parts
        week = get_week_by_key(db, wk)
        db.add(
            MealCompletion(
                user_id=user.id,
                week_id=week.id,
                day_of_week=day_to_index(day),
                slot_index=int(slot_s),
            )
        )
    db.commit()
    return {"ok": True}
