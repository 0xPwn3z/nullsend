"""SecureRelay backend configuration via pydantic-settings."""

from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderConfig(BaseModel):
    """LLM provider configuration."""

    name: str = "groq"
    model: str = "llama-3.1-8b-instant"
    base_url: str | None = None


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_prefix="SECURERELAY_",
        env_file="/data/.env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    provider: ProviderConfig = ProviderConfig()
    vault_db_path: Path = Path("/data/vault.db")
    audit_log_path: Path = Path("/data/audit.jsonl")
    vault_password: str = "changeme"
    session_ttl_hours: int = 24
    cors_origins: list[str] = ["http://localhost:3000"]
    max_response_tokens: int = 2048
    api_key: str = ""
