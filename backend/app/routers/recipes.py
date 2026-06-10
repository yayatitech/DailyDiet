from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import require_admin
from app.meals import normalize_meal_name
from app.models import RecipeCatalogEntry
from app.recipe_utils import recipe_has_internal_content, recipe_image_url
from app.schemas import IngredientOut, RecipeCreate, RecipeOut, RecipeSummary, RecipeUpdate

router = APIRouter(prefix="/v1", tags=["recipes"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def public_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "public"


def recipes_dir() -> Path:
    path = public_root() / "recipes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def entry_to_out(entry: RecipeCatalogEntry) -> RecipeOut:
    ingredients = [
        IngredientOut(amount=str(item.get("amount", "")), item=str(item.get("item", "")))
        for item in (entry.ingredients or [])
        if item.get("item")
    ]
    return RecipeOut(
        id=entry.id,
        name=entry.name,
        name_key=entry.name_key,
        display_name=entry.display_name,
        ingredients=ingredients,
        instructions=entry.instructions or "",
        image_url=recipe_image_url(entry.image_path),
        external_url=entry.external_url,
        has_content=recipe_has_internal_content(entry),
        updated_at=entry.updated_at,
    )


def entry_to_summary(entry: RecipeCatalogEntry) -> RecipeSummary:
    return RecipeSummary(
        id=entry.id,
        name=entry.name,
        display_name=entry.display_name,
        has_image=bool(entry.image_path),
        has_content=recipe_has_internal_content(entry),
    )


def apply_recipe_fields(entry: RecipeCatalogEntry, body: RecipeCreate | RecipeUpdate) -> None:
    if isinstance(body, RecipeCreate) or body.name is not None:
        name = (body.name if isinstance(body, RecipeCreate) else body.name).strip()
        entry.name = name
        entry.name_key = normalize_meal_name(name)
    if isinstance(body, RecipeCreate) or body.display_name is not None:
        display_name = body.display_name.strip() if body.display_name else None
        entry.display_name = display_name
    if isinstance(body, RecipeCreate) or body.ingredients is not None:
        entry.ingredients = [
            {"amount": ing.amount.strip(), "item": ing.item.strip()}
            for ing in (body.ingredients or [])
            if ing.item.strip()
        ]
    if isinstance(body, RecipeCreate) or body.instructions is not None:
        entry.instructions = (body.instructions or "").strip()
    if isinstance(body, RecipeCreate) or body.external_url is not None:
        external = (body.external_url or "").strip() if body.external_url else None
        entry.external_url = external
    entry.updated_at = datetime.utcnow()


def delete_recipe_image(entry: RecipeCatalogEntry) -> None:
    if not entry.image_path:
        return
    image_file = public_root() / entry.image_path
    if image_file.is_file():
        image_file.unlink(missing_ok=True)


@router.get("/recipes", response_model=list[RecipeSummary])
def list_recipes(db: Session = Depends(get_db)):
    rows = db.query(RecipeCatalogEntry).order_by(RecipeCatalogEntry.name).all()
    return [entry_to_summary(row) for row in rows]


@router.get("/recipes/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    entry = db.get(RecipeCatalogEntry, recipe_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return entry_to_out(entry)


@router.post("/admin/recipes", response_model=RecipeOut)
def create_recipe(
    body: RecipeCreate,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    name_key = normalize_meal_name(body.name)
    existing = db.query(RecipeCatalogEntry).filter(RecipeCatalogEntry.name_key == name_key).first()
    if existing:
        raise HTTPException(status_code=409, detail="Recipe name already exists")
    entry = RecipeCatalogEntry(
        name=body.name.strip(),
        name_key=name_key,
        ingredients=[],
        instructions="",
    )
    apply_recipe_fields(entry, body)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry_to_out(entry)


@router.patch("/admin/recipes/{recipe_id}", response_model=RecipeOut)
def update_recipe(
    recipe_id: int,
    body: RecipeUpdate,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    entry = db.get(RecipeCatalogEntry, recipe_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if body.name is not None:
        name_key = normalize_meal_name(body.name)
        conflict = (
            db.query(RecipeCatalogEntry)
            .filter(RecipeCatalogEntry.name_key == name_key, RecipeCatalogEntry.id != recipe_id)
            .first()
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Recipe name already exists")
    apply_recipe_fields(entry, body)
    db.commit()
    db.refresh(entry)
    return entry_to_out(entry)


@router.delete("/admin/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    entry = db.get(RecipeCatalogEntry, recipe_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Recipe not found")
    delete_recipe_image(entry)
    db.delete(entry)
    db.commit()
    return {"ok": True}


@router.post("/admin/recipes/{recipe_id}/image", response_model=RecipeOut)
async def upload_recipe_image(
    recipe_id: int,
    file: UploadFile = File(...),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    entry = db.get(RecipeCatalogEntry, recipe_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Recipe not found")

    content_type = file.content_type or ""
    ext = ALLOWED_IMAGE_TYPES.get(content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="Unsupported image type (use JPEG, PNG, or WebP)")

    data = await file.read()
    if len(data) > settings.max_recipe_image_bytes:
        raise HTTPException(status_code=400, detail="Image too large (max 5 MB)")

    delete_recipe_image(entry)
    filename = f"{recipe_id}{ext}"
    dest = recipes_dir() / filename
    dest.write_bytes(data)

    entry.image_path = f"recipes/{filename}"
    entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)
    return entry_to_out(entry)
