import pytest
from pydantic import ValidationError

from app.schemas import MealPatch, RegisterIn


class TestMealPatch:
    def test_valid_slot_index(self):
        patch = MealPatch(day="monday", slot_index=7, content="apple")
        assert patch.slot_index == 7

    def test_rejects_slot_index_8(self):
        with pytest.raises(ValidationError):
            MealPatch(day="monday", slot_index=8, content="apple")

    def test_rejects_negative_slot_index(self):
        with pytest.raises(ValidationError):
            MealPatch(day="monday", slot_index=-1, content="apple")


class TestRegisterIn:
    def test_valid_registration(self):
        reg = RegisterIn(email="user@example.com", password="password123")
        assert reg.password == "password123"

    def test_rejects_short_password(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="user@example.com", password="short")

    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="not-an-email", password="password123")
