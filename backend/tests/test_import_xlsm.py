from datetime import datetime

import import_xlsm


class TestNormalizeTime:
    def test_with_ampm(self):
        assert import_xlsm.normalize_time("6:30 AM") == "6:30 AM"

    def test_one_pm(self):
        assert import_xlsm.normalize_time("1 PM") == "1:00 PM"

    def test_bare_hour_guesses_am_pm(self):
        assert import_xlsm.normalize_time("8") == "8:00 AM"
        assert import_xlsm.normalize_time("1") == "1:00 PM"

    def test_empty(self):
        assert import_xlsm.normalize_time("") == ""


class TestParseMealLabel:
    def test_meal_with_time(self):
        slot_id, time_part = import_xlsm.parse_meal_label("Meal 1\n6:30 AM")
        assert slot_id == 1
        assert time_part == "6:30 AM"

    def test_garbage(self):
        assert import_xlsm.parse_meal_label("not a meal") == (None, "")

    def test_empty(self):
        assert import_xlsm.parse_meal_label("") == (None, "")


class TestParseStartDate:
    def test_full_month(self):
        result = import_xlsm.parse_start_date("January 6, 2025")
        assert result == datetime(2025, 1, 6)

    def test_abbreviated_month(self):
        result = import_xlsm.parse_start_date("Jan 15, 2025")
        assert result == datetime(2025, 1, 15)

    def test_empty(self):
        assert import_xlsm.parse_start_date("") is None

    def test_bad_date(self):
        assert import_xlsm.parse_start_date("Not A Date") is None


class TestTitleStartDate:
    def test_extracts_from_title(self):
        result = import_xlsm.title_start_date("Week 1 starting: January 6, 2025")
        assert result == datetime(2025, 1, 6)

    def test_missing_date(self):
        assert import_xlsm.title_start_date("Week 1") is None


class TestFormatStartDate:
    def test_formats_datetime(self):
        d = datetime(2025, 1, 6)
        assert import_xlsm.format_start_date(d) == "January 6, 2025"
