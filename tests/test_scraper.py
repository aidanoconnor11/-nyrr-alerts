from scraper import discover_event_urls, parse_openings


NYRR_MARKUP = '''
<ul class="race-list list-unstyled">
  <li><div class="category-box" data-filterable-status="AVL">
    <div class="category-name">Volunteer Leaders and Leaders in Training (NO +1)</div>
    <a class="category-register-btn" href="https://register.nyrr.org/?event=abc&amp;option=available">Register</a>
  </div></li>
  <li><div class="category-box" data-filterable-status="SOL">
    <div class="category-name">Bag Check</div>
  </div></li>
  <li><div class="category-box" data-filterable-status="MED">
    <div class="category-name">Medical Volunteers (must be licensed in NYS)</div>
    <a class="category-register-btn" href="https://register.nyrr.org/?event=abc&amp;option=medical">Register</a>
  </div></li>
</ul>
'''


def test_parse_supplied_nyrr_markup() -> None:
    openings = parse_openings(
        NYRR_MARKUP,
        "https://events.nyrr.org/nyrr-midnight-run-volunteers",
        frozenset({"AVL", "MED"}),
    )

    assert [(opening.role_name, opening.status) for opening in openings] == [
        ("Volunteer Leaders and Leaders in Training (NO +1)", "AVL"),
        ("Medical Volunteers (must be licensed in NYS)", "MED"),
    ]
    assert openings[0].register_url.startswith("https://register.nyrr.org/?event=")


def test_discover_event_urls_only_keeps_event_pages() -> None:
    html = '''
        <a href="https://events.nyrr.org/event-a">A</a>
        <a href="/event-b">Not an event host</a>
        <a href="https://nyrr.org/foo">Not an event host</a>
    '''
    assert discover_event_urls(html, "https://www.nyrr.org/getinvolved/volunteeropportunities") == {
        "https://events.nyrr.org/event-a"
    }
