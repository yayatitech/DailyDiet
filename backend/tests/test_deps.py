from datetime import date

import pytest
from fastapi import HTTPException

from app.deps import (
    day_to_index,
    index_to_day,
    parse_start_date,
    slot_content_from_import,
    week_detail_to_export_meals,
)
from app.schemas import MealItemOut, WeekDetail


class TestDayIndex:
    def test_round_trip(self):
        for i, day in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
            assert day_to_index(day) == i
            assert index_to_day(i) == day

    def test_invalid_day_raises(self):
        with pytest.raises(HTTPException) as exc:
            day_to_index("notaday")
        assert exc.value.status_code == 400


class TestParseStartDate:
    def test_full_month(self):
        result = parse_start_date("Week 1 starting: January 6, 2025")
        assert result == date(2025, 1, 6)

    def test_abbreviated_month(self):
        result = parse_start_date("Week 2 starting: Jan 15, 2025")
        assert result == date(2025, 1, 15)

    def test_no_match(self):
        assert parse_start_date("Week 1") is None

    def test_bad_date(self):
        assert parse_start_date("Week 1 starting: Not A Date") is None

    def test_empty_date_part(self):
        assert parse_start_date("Week 1 starting:   ") is None


class TestSlotContentFromImport:
    def test_plain_string(self):
        assert slot_content_from_import("apple\nbanana") == "apple\nbanana"

    def test_empty_list(self):
        assert slot_content_from_import([]) == ""

    def test_list_of_dicts(self):
        value = [{"text": "apple"}, {"text": "banana"}, {"text": ""}]
        assert slot_content_from_import(value) == "apple\nbanana"

    def test_list_of_strings(self):
        assert slot_content_from_import(["apple", "banana"]) == "apple\nbanana"

    def test_unknown_type_coerced(self):
        assert slot_content_from_import(42) == "42"


class TestWeekDetailToExportMeals:
    def test_flattens_enriched_items(self):
        detail = WeekDetail(
            id="week-1",
            title="Week 1",
            start_date=date(2025, 1, 6),
            notes="",
            meals={
                "monday": [
                    [MealItemOut(text="apple", recipe_url="https://a.com"), MealItemOut(text="banana")],
                    [],
                ],
                "tuesday": [[]],
                "wednesday": [[]],
                "thursday": [[]],
                "friday": [[]],
                "saturday": [[]],
                "sunday": [[]],
            },
        )
        exported = week_detail_to_export_meals(detail)
        assert exported["monday"][0] == "apple\nbanana"
        assert exported["monday"][1] == ""
