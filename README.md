# NYRR volunteer alerts

This is deliberately a small polling service: it fetches NYRR's volunteer event pages, looks for roles whose status is open, and emails only when a role changes from unavailable to available. It uses normal HTTP requests—not browser automation—and stores a tiny local JSON state file to prevent repeat alerts.

## How it works

1. Each run tries to discover event links from NYRR's volunteer directory.
2. It fetches every event page and reads each `.category-box` element's `data-filterable-status`.
3. `AVL` (available) and `MED` (medical available) are treated as open; a role is identified by its unique NYRR registration URL.
4. The run emails only links not present in the previous successful scan. When a role fills, it disappears from state, so reopening it later sends another alert.

NYRR's main directory sometimes sends automated requests through a waiting room. The monitor handles that gracefully: configure the event pages you care about in `NYRR_EVENT_URLS`, and it will continue to watch them even if discovery is temporarily blocked.

## GitHub Actions setup

The included workflow runs at minutes 7, 17, 27, 37, 47, and 57 of every hour (about every ten minutes). It keeps `state.json` committed in the repository, which is how a disposable GitHub runner knows which openings it has already alerted on.

Before enabling it, add one Actions secret:

1. In your Google Account, create an **App Password** for Mail (this requires two-step verification).
2. In this repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name it `GMAIL_APP_PASSWORD` and paste the app password. Do not use your regular Gmail password.

The workflow is already set to send from `aidanoconnor274@gmail.com` to the same address. Its monitored direct event pages live in the workflow file, which keeps them available even when NYRR's directory is behind a waiting room. To change the list later, edit `NYRR_EVENT_URLS` in that workflow.

```text
https://events.nyrr.org/nyrr-midnight-run-volunteers
```

This fallback matters because NYRR sometimes puts its directory behind a waiting room. The monitor will still attempt directory discovery for new races, but direct event URLs continue to work whenever that happens.

Commit and push the workflow to the repository's default branch, then use **Actions → Check NYRR volunteer openings → Run workflow** once. The first successful normal run alerts you about any roles already available; after that, only an availability change sends mail.

GitHub schedules are best-effort and can be delayed under high load, so this is an approximately-ten-minute checker rather than a hard real-time service. Scheduled workflows must live on the default branch; GitHub also disables schedules in inactive public repositories after 60 days. [GitHub’s scheduling documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) has the details.

## Local setup (optional)

For local testing, create a virtual environment and install the runtime dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

To run the parser tests, install `requirements-dev.txt` instead.

Run an initial check without sending mail or recording state:

```sh
NYRR_EVENT_URLS=https://events.nyrr.org/nyrr-midnight-run-volunteers \
  .venv/bin/python app.py --dry-run
```

Once the output looks right, run it normally. The first normal run treats currently available roles as new and emails them; after that, it alerts only on changes.

## Useful commands

```sh
# Test page parsing without changing state or emailing.
.venv/bin/python app.py --dry-run --event-url https://events.nyrr.org/nyrr-midnight-run-volunteers

# Send a one-time delivery test with the current scan summary; does not save state.
.venv/bin/python app.py --test-email --event-url https://events.nyrr.org/nyrr-midnight-run-volunteers

# Watch only a fixed set of pages (disable directory discovery).
NYRR_DIRECTORY_URL='' NYRR_EVENT_URLS='https://events.nyrr.org/example' .venv/bin/python app.py
```
