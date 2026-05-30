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


class WeekSummary(BaseModel):
    id: str
    title: str
    start_date: date | None = None


class WeekDetail(BaseModel):
    id: str
    title: str
    start_date: date | None = None
    notes: str
    meals: dict[str, list[str]]


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
