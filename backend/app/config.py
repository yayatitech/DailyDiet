from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://dailydiet:dailydiet@localhost:5432/dailydiet"
    jwt_secret: str = "dev-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    admin_api_key: str = "dev-admin-key"
    cors_origins: str = "http://localhost:5173,http://localhost:8081"
    default_dev_email: str = "dev@dailydiet.local"
    default_dev_password: str = "devpassword"
    public_dir: str = "../public"
    max_recipe_image_bytes: int = 5 * 1024 * 1024
    allow_anonymous_dev_user: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
