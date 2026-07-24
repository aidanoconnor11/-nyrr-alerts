"""One monitoring run. Schedule this command with cron or launchd."""

from __future__ import annotations

import argparse
import logging
import sys

from config import load_settings
from notifier import send_opening_email, send_test_email
from scraper import FetchError, Opening, discover_event_urls, fetch_html, parse_openings
from state import load_state, save_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Check NYRR volunteer roles and email new openings.")
    parser.add_argument("--dry-run", action="store_true", help="Print alerts but do not send email or save state.")
    parser.add_argument("--test-email", action="store_true", help="Send a scan summary email without saving state.")
    parser.add_argument("--event-url", action="append", default=[], help="Check this event page (may be repeated).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = load_settings()

    event_urls = set(settings.event_urls) | set(args.event_url)
    if settings.directory_url:
        try:
            directory = fetch_html(settings.directory_url, timeout=settings.timeout_seconds, user_agent=settings.user_agent)
            discovered = discover_event_urls(directory, settings.directory_url)
            event_urls |= discovered
            logging.info("Discovered %d event pages from NYRR's directory", len(discovered))
        except FetchError as exc:
            # Direct event URLs still work when NYRR's directory is behind a waiting room.
            logging.warning("Could not refresh NYRR directory: %s", exc)

    if not event_urls:
        logging.error("No event URLs available. Set NYRR_EVENT_URLS or NYRR_DIRECTORY_URL.")
        return 2

    current: dict[str, Opening] = {}
    failed_urls: set[str] = set()
    for url in sorted(event_urls):
        try:
            html = fetch_html(url, timeout=settings.timeout_seconds, user_agent=settings.user_agent)
            for opening in parse_openings(html, url, settings.open_statuses):
                current[opening.key] = opening
        except FetchError as exc:
            failed_urls.add(url)
            logging.warning("Skipping %s: %s", url, exc)

    if len(failed_urls) == len(event_urls):
        logging.error("Every event-page request failed; state was left untouched.")
        return 1

    state = load_state(settings.state_file)
    previous = state["openings"]
    # A transient failure must not make an existing opening look filled. Keep
    # those entries until that specific event page has a successful scan.
    for key, opening in previous.items():
        if opening.get("event_url") in failed_urls:
            current[key] = Opening(key=key, **opening)
    new_openings = [opening for key, opening in current.items() if key not in previous]
    logging.info("Found %d open roles; %d are newly open", len(current), len(new_openings))

    if args.test_email:
        if not settings.email_configured:
            logging.error("Email is not configured; state was left untouched.")
            return 2
        send_test_email(settings, current.values())
        logging.info("Test email sent to %s", ", ".join(settings.email_to))
        return 0

    if new_openings:
        if args.dry_run:
            for opening in new_openings:
                print(f"NEW: {opening.event_name} — {opening.role_name}: {opening.register_url}")
        elif not settings.email_configured:
            logging.error("New openings found, but email is not configured; state was left untouched.")
            return 2
        else:
            send_opening_email(settings, new_openings)
            logging.info("Alert email sent to %s", ", ".join(settings.email_to))

    if not args.dry_run:
        save_state(settings.state_file, {key: opening.as_dict() for key, opening in current.items()})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # scheduler-visible error without a long traceback
        logging.error("NYRR alert run failed: %s", exc)
        raise SystemExit(1)
