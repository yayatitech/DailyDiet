from app.config import Settings


class TestCorsOriginList:
    def test_splits_and_trims(self):
        s = Settings(cors_origins="http://a.com, http://b.com ,http://c.com")
        assert s.cors_origin_list == ["http://a.com", "http://b.com", "http://c.com"]

    def test_drops_empty_entries(self):
        s = Settings(cors_origins="http://a.com,, ,http://b.com")
        assert s.cors_origin_list == ["http://a.com", "http://b.com"]
