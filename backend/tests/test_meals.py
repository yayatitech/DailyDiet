from app.meals import enrich_items, join_slot_content, normalize_meal_name, split_slot_content
from app.schemas import MealItemOut


class TestNormalizeMealName:
    def test_trims_and_lowercases(self):
        assert normalize_meal_name("  Oatmeal  ") == "oatmeal"

    def test_collapses_whitespace(self):
        assert normalize_meal_name("Green   Tea") == "green tea"


class TestSplitSlotContent:
    def test_empty_string(self):
        assert split_slot_content("") == []

    def test_strips_blank_lines(self):
        assert split_slot_content("apple\n\nbanana\n  \n") == ["apple", "banana"]

    def test_preserves_order(self):
        assert split_slot_content("first\nsecond\nthird") == ["first", "second", "third"]


class TestJoinSlotContent:
    def test_joins_non_empty_items(self):
        items = [MealItemOut(text="apple"), MealItemOut(text="banana")]
        assert join_slot_content(items) == "apple\nbanana"

    def test_skips_empty_text(self):
        items = [MealItemOut(text="apple"), MealItemOut(text="  "), MealItemOut(text="banana")]
        assert join_slot_content(items) == "apple\nbanana"

    def test_empty_list(self):
        assert join_slot_content([]) == ""


class TestEnrichItems:
    def test_catalog_hit(self):
        catalog = {"oatmeal": "https://example.com/oatmeal"}
        result = enrich_items("Oatmeal", catalog)
        assert len(result) == 1
        assert result[0].text == "Oatmeal"
        assert result[0].recipe_url == "https://example.com/oatmeal"

    def test_catalog_miss(self):
        result = enrich_items("Unknown Food", {})
        assert len(result) == 1
        assert result[0].recipe_url is None

    def test_case_insensitive_match(self):
        catalog = {"green tea": "https://example.com/tea"}
        result = enrich_items("Green   Tea", catalog)
        assert result[0].recipe_url == "https://example.com/tea"

    def test_empty_content(self):
        assert enrich_items("", {"x": "y"}) == []

    def test_multiple_lines(self):
        catalog = {"apple": "https://a.com", "banana": "https://b.com"}
        result = enrich_items("apple\nbanana", catalog)
        assert len(result) == 2
        assert result[0].recipe_url == "https://a.com"
        assert result[1].recipe_url == "https://b.com"
