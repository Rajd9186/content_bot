import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    # --- Database ---
    # Use PostgreSQL in production (set via DATABASE_URL env var).
    # Falls back to SQLite for local dev if no DATABASE_URL is set.
    database_url: str = "sqlite+aiosqlite:///./verified_ai.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_pre_ping: bool = True
    database_echo: bool = False

    # --- LLM ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"
    ollama_api_key: str = ""
    ollama_model: str = "nemotron-3-super:cloud"

    # --- Search ---
    tavily_api_key: Optional[str] = None

    # --- App ---
    secret_key: str = "change-me-in-production"
    environment: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Verified AI Research Writer"
    project_version: str = "1.0.0"

    # --- Workflow ---
    max_workflow_retries: int = 3
    research_concurrency: int = 10
    workflow_retry_delay: float = 1.0
    workflow_event_buffer_size: int = 50
    workflow_event_flush_interval: float = 2.0
    sse_keepalive_interval: float = 15.0
    sse_recent_event_limit: int = 100

    # Stage weights for overall progress calculation (must sum to 100)
    # Aligned with the 9-stage pipeline: Planning -> Research -> Synthesis ->
    # Outlining -> Writing -> Validation -> SEO -> FactCheck -> Finalization
    stage_weights: dict[str, float] = {
        "INIT": 0.0,
        "PLANNING": 10.0,
        "RESEARCH": 25.0,
        "SYNTHESIS": 35.0,
        "OUTLINING": 45.0,
        "WRITING": 55.0,
        "VALIDATION": 65.0,
        "SEO": 75.0,
        "FACT_CHECK": 85.0,
        "FINALIZATION": 95.0,
        "PUBLISHED": 100.0,
    }

    # --- Event Bus Architecture ---
    # The platform uses an in-process asyncio.Queue broadcast backed by
    # PostgreSQL persistence (see app.events.event_bus and
    # app.services.event_bus).  Redis is NOT used for event distribution.
    # Trade-off: Zero external deps + DB replay, but no horizontal scaling.
    # To add Redis: set redis_url below and install redis[hiredis].
    redis_url: str = ""

    # --- Domain Trust ---
    trusted_domains: list[str] = [
        "reuters.com", "who.int", "nasa.gov", "nih.gov", "cdc.gov",
        "un.org", "worldbank.org", "imf.org", "ieee.org", "acm.org",
        "nature.com", "science.org", "oxford.ac.uk", "cam.ac.uk",
        "harvard.edu", "mit.edu", "stanford.edu", "berkeley.edu",
    ]

    domain_trust_scores: dict[str, float] = {
        "reuters.com": 0.95, "who.int": 0.93, "nasa.gov": 0.95,
        "nih.gov": 0.94, "cdc.gov": 0.93, "un.org": 0.90,
        "worldbank.org": 0.92, "imf.org": 0.92, "ieee.org": 0.88,
        "acm.org": 0.87, "nature.com": 0.92, "science.org": 0.91,
        "harvard.edu": 0.90, "mit.edu": 0.90, "stanford.edu": 0.90,
        "cam.ac.uk": 0.88, "oxford.ac.uk": 0.88,
    }

    default_trust_score: float = 0.60
    high_trust_threshold: float = 0.85
    medium_trust_threshold: float = 0.70

    model_class: str = "pkl"
    max_retries: int = 3
    retry_delay: float = 1.0


settings = Settings()
