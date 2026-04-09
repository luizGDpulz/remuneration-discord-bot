from __future__ import annotations

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ValueError(f"The environment variable {name} is required.")
    return value.strip()


def _optional_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"The environment variable {name} must be an integer.") from exc


@dataclass(slots=True)
class Settings:
    discord_bot_token: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    timezone_name: str = "UTC"
    log_level: str = "INFO"
    sync_guild_id: int | None = None
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        db_port = _optional_int("DB_PORT") or 3306
        db_pool_min_size = _optional_int("DB_POOL_MIN_SIZE") or 1
        db_pool_max_size = _optional_int("DB_POOL_MAX_SIZE") or 10

        timezone_name = os.getenv("TZ", "UTC").strip() or "UTC"
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"The timezone '{timezone_name}' configured in TZ is invalid."
            ) from exc

        if db_pool_min_size > db_pool_max_size:
            raise ValueError("DB_POOL_MIN_SIZE cannot be greater than DB_POOL_MAX_SIZE.")

        return cls(
            discord_bot_token=_require_env("DISCORD_BOT_TOKEN"),
            db_host=_require_env("DB_HOST"),
            db_port=db_port,
            db_name=_require_env("DB_NAME"),
            db_user=_require_env("DB_USER"),
            db_password=_require_env("DB_PASSWORD"),
            timezone_name=timezone_name,
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
            sync_guild_id=_optional_int("DISCORD_SYNC_GUILD_ID"),
            db_pool_min_size=db_pool_min_size,
            db_pool_max_size=db_pool_max_size,
        )

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name)

    @property
    def masked_database_url(self) -> str:
        return (
            f"mariadb://{self.db_user}:***@{self.db_host}:{self.db_port}/{self.db_name}"
        )
