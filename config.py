"""Configuration read from environment variables.

Keeping secrets in the environment means they never need to be committed to
the repository. Copy `.env.example` into your password manager or scheduler
configuration; this module intentionally does not load `.env` files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DIRECTORY_URL = "https://www.nyrr.org/getinvolved/volunteeropportunities"


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    event_urls: tuple[str, ...]
    directory_url: str | None
    open_statuses: frozenset[str]
    state_file: Path
    timeout_seconds: int
    user_agent: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    email_from: str | None
    email_to: tuple[str, ...]
    smtp_use_ssl: bool

    @property
    def email_configured(self) -> bool:
        return bool(self.smtp_host and self.email_from and self.email_to)


def load_settings() -> Settings:
    directory_url = os.getenv("NYRR_DIRECTORY_URL", DEFAULT_DIRECTORY_URL).strip() or None
    return Settings(
        event_urls=_csv("NYRR_EVENT_URLS"),
        directory_url=directory_url,
        open_statuses=frozenset(status.upper() for status in _csv("NYRR_OPEN_STATUSES", "AVL,MED")),
        state_file=Path(os.getenv("NYRR_STATE_FILE", "state.json")),
        timeout_seconds=int(os.getenv("NYRR_TIMEOUT_SECONDS", "20")),
        user_agent=os.getenv("NYRR_USER_AGENT", "NYRR volunteer availability notifier/1.0"),
        smtp_host=os.getenv("SMTP_HOST") or None,
        smtp_port=int(os.getenv("SMTP_PORT", "465")),
        smtp_username=os.getenv("SMTP_USERNAME") or None,
        smtp_password=os.getenv("SMTP_PASSWORD") or None,
        email_from=os.getenv("EMAIL_FROM") or None,
        email_to=_csv("EMAIL_TO"),
        smtp_use_ssl=_bool("SMTP_USE_SSL", True),
    )
