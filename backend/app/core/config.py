from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core
    environment: str = "development"
    debug: bool = False
    demo_mode: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./data/playbooks.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    api_prefix: str = "/api/v1"

    # CORS
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # JWT
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    gemini_max_tokens: int = 2048
    gemini_temperature: float = 0.2
    gemini_timeout_seconds: int = 30
    gemini_cache_enabled: bool = True
    gemini_cache_path: str = "./data/gemini_cache.json"

    # Lobster Trap
    lobstertrap_binary_path: str = "./bin/lobstertrap"
    lobstertrap_log_dir: str = "./logs/lobstertrap"
    lobstertrap_policy_dir: str = "./policies"
    lobstertrap_config_path: str = "./config/lobstertrap.yaml"

    # Log Tailer
    log_dir: str = "./logs/lobstertrap"
    log_glob_pattern: str = "events.*.log"
    log_poll_interval: float = 0.1
    log_max_backfill_bytes: int = 1_048_576

    # Detection
    anomaly_threshold: float = 25.0
    max_anomaly_score: float = 100.0

    # Playbooks
    playbook_dir: str = "./policies"
    playbook_auto_execute: bool = True
    playbook_human_review_sla_minutes: int = 30

    # Forensics
    evidence_store_path: str = "./evidence"
    evidence_retention_days: int = 2555
    forensics_enabled: bool = True

    # Security
    sqlcipher_key: Optional[str] = None
    retain_full_prompts: bool = False

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100

    # Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst_size: int = 10

    # Judge Layer
    judge_deterministic_mode: bool = True
    judge_bypass_detection: bool = True

    # SupraWall
    suprawall_webhook_url: Optional[str] = None

    # Policy Builder
    policy_builder_enabled: bool = True
    nist_baseline_path: str = "./data/nist_baselines.json"
    odp_defaults_path: str = "./data/odp_defaults.json"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_demo_mode(self) -> bool:
        return self.demo_mode

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key) and not self.demo_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
