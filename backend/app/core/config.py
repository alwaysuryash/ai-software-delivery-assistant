"""Application configuration.

All configuration is environment-driven (12-factor). Nothing sensitive is hard-coded.
Secrets are *referenced* here but resolved through the ``SecretProvider`` port at runtime
(BRD §16: never store connector secrets in prompts or source control).
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class ModelProviderKind(StrEnum):
    AZURE_OPENAI = "azure_openai"
    FAKE = "fake"


class SecretProviderKind(StrEnum):
    ENV = "env"
    AZURE_KEY_VAULT = "azure_key_vault"


class RetrievalProviderKind(StrEnum):
    PGVECTOR = "pgvector"
    AZURE_AI_SEARCH = "azure_ai_search"


class AuthProviderKind(StrEnum):
    DEV = "dev"
    ENTRA_ID = "entra_id"


class ConnectorMode(StrEnum):
    MOCK = "mock"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # App
    app_env: AppEnv = AppEnv.LOCAL
    app_name: str = "AI Software Delivery Assistant"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:3000"

    # Database / cache
    database_url: str = "postgresql+asyncpg://aisda:aisda_dev_pw@localhost:5432/aisda"
    redis_url: str = "redis://localhost:6379/0"

    # Model provider
    model_provider: ModelProviderKind = ModelProviderKind.FAKE
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"

    # Secrets / retrieval
    secret_provider: SecretProviderKind = SecretProviderKind.ENV
    azure_key_vault_url: str = ""
    retrieval_provider: RetrievalProviderKind = RetrievalProviderKind.PGVECTOR

    # Auth
    auth_provider: AuthProviderKind = AuthProviderKind.DEV
    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_client_secret: str = ""
    jwt_signing_secret: str = "change-me-in-prod-please-32bytes-min"

    # Feature flags / kill switches (BRD §16)
    feature_write_actions_enabled: bool = False
    feature_multi_agent_enabled: bool = False

    # Connectors
    connector_mode: ConnectorMode = ConnectorMode.MOCK

    # Observability
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "aisda-backend"

    # Agent execution guardrails (BRD §16, Phase 4/5)
    agent_max_tool_calls: int = Field(default=12, ge=1, le=100)
    agent_timeout_seconds: int = Field(default=45, ge=5, le=300)
    orchestrator_max_steps: int = Field(default=25, ge=1, le=200)

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PROD


@lru_cache
def get_settings() -> Settings:
    """Cached singleton settings accessor."""
    return Settings()
