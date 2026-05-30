from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.meals import normalize_meal_name
from app.models import RecipeCatalogEntry
from app.schemas import RecipeCreate, RecipeOut, RecipeUpdate

router = APIRouter(prefix="/v1", tags=["recipes"])


@router.get("/recipes", response_model=list[RecipeOut])
def list_recipes(db: Session = Depends(get_db)):
    return db.query(RecipeCatalogEntry).order_by(RecipeCatalogEntry.name).all()


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
    entry = RecipeCatalogEntry(name=body.name.strip(), name_key=name_key, recipe_url=body.recipe_url.strip())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


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
        entry.name = body.name.strip()
        entry.name_key = name_key
    if body.recipe_url is not None:
        entry.recipe_url = body.recipe_url.strip()
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/admin/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    entry = db.get(RecipeCatalogEntry, recipe_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}
