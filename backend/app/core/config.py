from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Поиск Источников"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24

    postgres_dsn: str = "postgresql://ruby:ruby@postgredb:5432/postgres"

    milvus_host: str = "standalone"
    milvus_port: int = 19530

    storage_dir: Path = Path("/data/storage")
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    panel_email: str = Field(
        default="operator@example.com",
        validation_alias=AliasChoices("PANEL_EMAIL", "ADMIN_EMAIL"),
    )
    panel_password: str = Field(
        default="operator",
        validation_alias=AliasChoices("PANEL_PASSWORD", "ADMIN_PASSWORD"),
    )

    use_custom_llm: bool = Field(
        default=False,
        validation_alias=AliasChoices("USE_CUSTOM_LLM", "use_custom_llm"),
    )
    custom_llm_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CUSTOM_LLM_ENDPOINT", "custom_llm_endpoint"),
    )


settings = Settings()
