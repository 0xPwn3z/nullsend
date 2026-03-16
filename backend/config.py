"""Nullsend backend configuration via pydantic-settings."""

from pathlib import Path

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderConfig(BaseModel):
    """LLM provider configuration."""

    name: str = "groq"
    model: str = "llama-3.1-8b-instant"
    base_url: str | None = None


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_prefix="NULLSEND_",
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

    # FIX: session expiry — TTL enforcement + startup cleanup
    @field_validator("vault_password", mode="before")
    @classmethod
    def validate_vault_password(cls, value: object) -> object:
        generate_cmd = 'python -c "import secrets; print(secrets.token_urlsafe(32))"'
        if value is None:
            raise ValueError(
                f"vault_password must be a strong secret (min 16 chars); generate one with: {generate_cmd}"
            )

        raw_value = str(value)
        if raw_value.strip().lower() in {"changeme", "change-me", "password", "secret", ""}:
            raise ValueError(
                f"vault_password is too weak; generate one with: {generate_cmd}"
            )

        if len(raw_value) < 16:
            raise ValueError(
                f"vault_password must be at least 16 characters; generate one with: {generate_cmd}"
            )

        return value
