from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    model_path: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("RERANKER_MODEL_PATH", "MODEL_PATH"),
    )
    base_model: str = Field(
        default="cointegrated/rubert-tiny2",
        validation_alias=AliasChoices("RERANKER_BASE_MODEL", "BASE_MODEL"),
    )
    max_length: int = Field(default=256, validation_alias=AliasChoices("RERANKER_MAX_LENGTH", "MAX_LENGTH"))


settings = Settings()
