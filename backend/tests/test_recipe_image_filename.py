from app.recipe_utils import recipe_image_url, recipe_stored_image_path, sanitize_recipe_image_filename


class TestSanitizeRecipeImageFilename:
    def test_preserves_sanitized_basename_with_content_type_ext(self):
        assert (
            sanitize_recipe_image_filename("pumkin-aloo-tikki.png", ".jpg", 42)
            == "pumkin-aloo-tikki.jpg"
        )

    def test_uses_basename_only(self):
        assert sanitize_recipe_image_filename("uploads/hero/photo.webp", ".jpg", 7) == "photo.jpg"

    def test_strips_windows_path(self):
        assert (
            sanitize_recipe_image_filename(r"C:\temp\photos\saag.jpg", ".jpg", 7) == "saag.jpg"
        )

    def test_blocks_path_traversal_to_basename(self):
        assert sanitize_recipe_image_filename("../../etc/passwd", ".jpg", 9) == "passwd.jpg"

    def test_replaces_unsafe_characters(self):
        assert sanitize_recipe_image_filename("My Photo (1).PNG", ".jpg", 3) == "My-Photo-1.jpg"

    def test_fallback_when_name_missing(self):
        assert sanitize_recipe_image_filename(None, ".jpg", 42) == "42.jpg"
        assert sanitize_recipe_image_filename("", ".png", 42) == "42.png"
        assert sanitize_recipe_image_filename("   ", ".webp", 42) == "42.webp"

    def test_fallback_when_name_invalid_after_sanitize(self):
        assert sanitize_recipe_image_filename("...", ".jpg", 5) == "5.jpg"
        assert sanitize_recipe_image_filename("???.png", ".jpg", 5) == "5.jpg"
        assert sanitize_recipe_image_filename(".", ".jpg", 5) == "5.jpg"
        assert sanitize_recipe_image_filename("..", ".jpg", 5) == "5.jpg"

    def test_truncates_long_stem(self):
        stem = "a" * 300
        result = sanitize_recipe_image_filename(f"{stem}.png", ".jpg", 1)
        assert result.endswith(".jpg")
        assert len(result) <= 184
        assert result.startswith("a")

    def test_stored_path_and_client_url(self):
        filename = sanitize_recipe_image_filename("dal-makhani.jpg", ".jpg", 12)
        path = recipe_stored_image_path(filename)
        assert path == "recipes/dal-makhani.jpg"
        assert recipe_image_url(path) == "/static/recipes/dal-makhani.jpg"

    def test_legacy_id_path_still_maps_to_static_url(self):
        assert recipe_image_url("recipes/42.jpg") == "/static/recipes/42.jpg"
