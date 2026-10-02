"""Fetch NYRR pages and extract currently registerable volunteer roles."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Opening:
    key: str
    event_name: str
    role_name: str
    status: str
    register_url: str
    event_url: str

    def as_dict(self) -> dict[str, str]:
        return {
            "event_name": self.event_name,
            "role_name": self.role_name,
            "status": self.status,
            "register_url": self.register_url,
            "event_url": self.event_url,
        }


def fetch_html(url: str, *, timeout: int, user_agent: str) -> str:
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": user_agent})
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Could not fetch {url}: {exc}") from exc
    return response.text


def discover_event_urls(html: str, source_url: str) -> set[str]:
    """Extract NYRR event pages from the public volunteer directory."""
    soup = BeautifulSoup(html, "html.parser")
    urls: set[str] = set()
    for anchor in soup.select("a[href]"):
        candidate = urljoin(source_url, anchor["href"])
        parsed = urlparse(candidate)
        if _is_event_url(parsed.netloc, parsed.path):
            urls.add(candidate.split("#", 1)[0])
    return urls


def parse_openings(html: str, event_url: str, open_statuses: frozenset[str]) -> list[Opening]:
    soup = BeautifulSoup(html, "html.parser")
    event_name = _event_name(soup, event_url)
    openings: list[Opening] = []
    for box in soup.select(".category-box[data-filterable-status]"):
        status = box.get("data-filterable-status", "").upper()
        if status not in open_statuses:
            continue
        register = box.select_one("a.category-register-btn[href]")
        role = box.select_one(".category-name")
        if not register or not role:
            continue
        role_name = role.get_text(" ", strip=True)
        register_url = urljoin(event_url, register["href"])
        # The registration link contains NYRR's stable event/option identifiers.
        key = register_url
        openings.append(Opening(key, event_name, role_name, status, register_url, event_url))
    if openings or soup.select_one(".category-box"):
        return openings

    # NYRR's current site renders registration options as articles instead of
    # the legacy ``.category-box`` elements. The visible labels map to the
    # legacy status codes so existing NYRR_OPEN_STATUSES settings keep working.
    for option in soup.select("article"):
        register = option.select_one('a[href*="register.nyrr.org"]')
        role = option.select_one("h3")
        if not register or not role:
            continue
        status = _current_status(option)
        if status not in open_statuses:
            continue
        role_name = role.get_text(" ", strip=True)
        register_url = urljoin(event_url, register["href"])
        openings.append(Opening(register_url, event_name, role_name, status, register_url, event_url))
    return openings


def _is_event_url(host: str, path: str) -> bool:
    if host == "events.nyrr.org":
        return bool(path.strip("/"))
    return host == "www.nyrr.org" and path.startswith("/races-and-events/") and path.rstrip("/").endswith("-volunteers")


def _current_status(option: BeautifulSoup) -> str:
    labels = {
        "AVAILABLE": "AVL",
        "NEAR CAPACITY": "MED",
        "LIMITED AVAILABILITY": "MED",
    }
    for text in option.stripped_strings:
        status = labels.get(text.upper())
        if status:
            return status
    return ""


def _event_name(soup: BeautifulSoup, event_url: str) -> str:
    heading = soup.select_one("h1")
    if heading and heading.get_text(strip=True):
        return heading.get_text(" ", strip=True)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return title.split("|")[0].strip()
    return urlparse(event_url).path.strip("/").replace("-", " ").title()
