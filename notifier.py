"""Email delivery for new NYRR volunteer openings."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable

from config import Settings
from scraper import Opening


def send_opening_email(settings: Settings, openings: Iterable[Opening]) -> None:
    openings = list(openings)
    message = EmailMessage()
    message["Subject"] = f"NYRR volunteer opening: {len(openings)} new"
    message["From"] = settings.email_from
    message["To"] = ", ".join(settings.email_to)
    message.set_content(_body(openings))

    smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=30) as client:
        if not settings.smtp_use_ssl:
            client.starttls()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password or "")
        client.send_message(message)


def send_test_email(settings: Settings, openings: Iterable[Opening]) -> None:
    """Confirm SMTP delivery without changing availability state."""
    openings = list(openings)
    message = EmailMessage()
    message["Subject"] = "NYRR volunteer alerts: delivery test"
    message["From"] = settings.email_from
    message["To"] = ", ".join(settings.email_to)
    summary = f"Current scan found {len(openings)} open role(s)."
    details = "\n".join(
        f"- {opening.event_name} — {opening.role_name}: {opening.register_url}"
        for opening in openings
    )
    message.set_content(f"This is a delivery test. {summary}\n\n{details or 'No openings found.'}")

    smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=30) as client:
        if not settings.smtp_use_ssl:
            client.starttls()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password or "")
        client.send_message(message)


def _body(openings: list[Opening]) -> str:
    lines = ["A previously unavailable NYRR volunteer role is now open:", ""]
    for opening in openings:
        lines.extend((
            f"{opening.event_name} — {opening.role_name} ({opening.status})",
            f"Register: {opening.register_url}",
            f"Event page: {opening.event_url}",
            "",
        ))
    lines.append("Act quickly: availability can change before registration completes.")
    return "\n".join(lines)
