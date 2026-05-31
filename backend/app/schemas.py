from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

DayKey = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]

DAY_KEYS: list[DayKey] = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]


class TimeSlotOut(BaseModel):
    id: int
    label: str
    time: str

    model_config = {"from_attributes": True}


class MealItemOut(BaseModel):
    text: str
    recipe_id: int | None = None
    recipe_url: str | None = None
    recipe_external: bool = False


class WeekSummary(BaseModel):
    id: str
    title: str
    start_date: date | None = None


class WeekDetail(BaseModel):
    id: str
    title: str
    start_date: date | None = None
    notes: str
    meals: dict[str, list[list[MealItemOut]]]


class MealPatch(BaseModel):
    day: DayKey
    slot_index: int = Field(ge=0, le=7)
    content: str


class NotesPatch(BaseModel):
    notes: str


class CompletionToggle(BaseModel):
    day: DayKey
    slot_index: int = Field(ge=0, le=7)
    completed: bool


class CompletionOut(BaseModel):
    day: DayKey
    slot_index: int
    completed: bool


class ExportBundle(BaseModel):
    plan: dict
    tracking: dict[str, bool]
    exported_at: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr

    model_config = {"from_attributes": True}


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class IngredientIn(BaseModel):
    amount: str = ""
    item: str = Field(min_length=1, max_length=255)


class IngredientOut(BaseModel):
    amount: str = ""
    item: str


class RecipeSummary(BaseModel):
    id: int
    name: str
    display_name: str | None = None
    has_image: bool = False
    has_content: bool = False

    model_config = {"from_attributes": True}


class RecipeOut(BaseModel):
    id: int
    name: str
    name_key: str
    display_name: str | None = None
    ingredients: list[IngredientOut] = Field(default_factory=list)
    instructions: str = ""
    image_url: str | None = None
    external_url: str | None = None
    has_content: bool = False
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RecipeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    ingredients: list[IngredientIn] = Field(default_factory=list)
    instructions: str = ""
    external_url: str | None = Field(default=None, max_length=2048)


class RecipeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    ingredients: list[IngredientIn] | None = None
    instructions: str | None = None
    external_url: str | None = Field(default=None, max_length=2048)
