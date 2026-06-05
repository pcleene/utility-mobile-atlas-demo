"""Centralised settings.

`pydantic-settings` reads from `.env` and process env. Every other module
imports `settings` from here; nobody else should call `os.getenv`.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Mongo -----------------------------------------------------------
    mongodb_uri: str = Field(...)
    mongodb_db: str = "UtilityApp"

    # --- Voyage / AutoEmbed ---------------------------------------------
    # The API key is consumed by Atlas project-level credentials. The seed
    # script keeps it here only so dev tooling stays in one place.
    voyage_api_key: str = ""
    voyage_model: str = "voyage-4-large"
    voyage_dimensions: int = 1024

    # --- CORS ------------------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://localhost:4173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- Demo / seed knobs ----------------------------------------------
    demo_customer_id: str = "CUST-MY-00184729"

    seed_customers: int = 1_000_000
    seed_transactions: int = 10_000_000
    seed_embedded_tickets: int = 2_000
    seed_timeseries_days: int = 60
    seed_timeseries_interval_minutes: int = 30

    enable_sharding: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
