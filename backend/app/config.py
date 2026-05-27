from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql://healthquest:healthquest@localhost:5432/healthquest"
    bot_token: str = ""
    webapp_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"
    dev_telegram_user_id: int = 100001
    dev_telegram_first_name: str = "Dev"
    bot_mode: str = "polling"
    webhook_base_url: str = ""
    webhook_secret: str = ""
    init_data_max_age_seconds: int = 86400
    gemini_api_key: str | None = None
    gemini_model: str = "models/gemini-2.5-flash"
    use_gemini_stub: bool = False
    ai_summary_provider: str = "g4f"  # g4f или gemini
    ai_summary_model: str = "gpt-3.5-turbo"  # модель для g4f
    ai_summary_timeout: int = 10

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
