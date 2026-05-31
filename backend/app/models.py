import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_index: Mapped[int] = mapped_column(Integer, unique=True)
    label: Mapped[str] = mapped_column(String(64))
    time_label: Mapped[str] = mapped_column(String(32))


class PlanTemplate(Base):
    __tablename__ = "plan_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(255), default="meal-plan.json")

    weeks: Mapped[list["TemplateWeek"]] = relationship(back_populates="template")


class TemplateWeek(Base):
    __tablename__ = "template_weeks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("plan_templates.id"))
    week_key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    week_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    template: Mapped["PlanTemplate"] = relationship(back_populates="weeks")
    meals: Mapped[list["TemplateMeal"]] = relationship(back_populates="week", cascade="all, delete-orphan")


class TemplateMeal(Base):
    __tablename__ = "template_meals"
    __table_args__ = (UniqueConstraint("week_id", "day_of_week", "slot_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("template_weeks.id"))
    day_of_week: Mapped[int] = mapped_column(Integer)
    slot_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, default="")

    week: Mapped["TemplateWeek"] = relationship(back_populates="meals")


class UserMealOverride(Base):
    __tablename__ = "user_meal_overrides"
    __table_args__ = (UniqueConstraint("user_id", "week_id", "day_of_week", "slot_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("template_weeks.id"))
    day_of_week: Mapped[int] = mapped_column(Integer)
    slot_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)


class UserWeekNotes(Base):
    __tablename__ = "user_week_notes"
    __table_args__ = (UniqueConstraint("user_id", "week_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("template_weeks.id"))
    notes: Mapped[str] = mapped_column(Text, default="")


class RecipeCatalogEntry(Base):
    __tablename__ = "recipe_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    name_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ingredients: Mapped[list] = mapped_column(JSONB, default=list)
    instructions: Mapped[str] = mapped_column(Text, default="")
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MealCompletion(Base):
    __tablename__ = "meal_completions"
    __table_args__ = (UniqueConstraint("user_id", "week_id", "day_of_week", "slot_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("template_weeks.id"))
    day_of_week: Mapped[int] = mapped_column(Integer)
    slot_index: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
