"""Build the static events.sarawak.news site into dist/.

Reads data/events-2026.json, renders dist/index.html (all twelve month
panels pre-rendered, current MYT month visible) and dist/about.html, and
copies site/ assets. No dependencies beyond the standard library.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import events_lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kit.python.analytics_loader import (  # noqa: E402
    ANALYTICS_LOADER_ATTR,
    render_analytics_loader as kit_render_analytics_loader,
)
from kit.python.analytics_registry import AnalyticsRegistry, load_analytics  # noqa: E402
from kit.python.shell import (  # noqa: E402
    NavItem,
    fleet_cross_link_items,
    render_back_to_top,
    render_footer as kit_render_footer,
    render_header as kit_render_header,
)

DATA = ROOT / "data" / "events.json"
SITE_CONFIG = ROOT / "data" / "site.json"
ANALYTICS_CONFIG = ROOT / "data" / "analytics.json"
SITE = ROOT / "site"
DIST = ROOT / "dist"
MYT = dt.timezone(dt.timedelta(hours=8))
YEAR = 2026
SITE_ORIGIN = "https://events.sarawak.news"
GA_ID = re.compile(r"G-[A-Z0-9]+\Z")
M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FULL = ["January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"]
NOTE = "Dates subject to change, check with organisers."
FOOTER_NOTE = "An independent listing of events across Sarawak."
# Site title, tagline, description, and About lead live only in data/site.json.
SITE_COPY_FIELDS = ("title", "tagline", "description", "about_lead")
FOOTER_CATEGORIES_INNER = """<h2 class="site-footer-categories-title">Categories</h2>
        <ul>
          <li><a class="site-footer-link" href="/?event_type=festival">Festival</a></li>
          <li><a class="site-footer-link" href="/?event_type=sports">Sports</a></li>
          <li><a class="site-footer-link" href="/?event_type=cultural">Cultural</a></li>
          <li><a class="site-footer-link" href="/?event_type=concert">Concert</a></li>
        </ul>"""
FOOTER_CREDIT = (
    'Built by <a class="site-footer-link site-footer-credit-link" href="https://hafiy.my" '
    'target="_blank" rel="noopener noreferrer">hafiy.my</a>, an independent publication. '
    "Not affiliated with the Sarawak Government."
)
FLEET_SITE_ID = "events"
e = html.escape


def render_fleet_network_section(fleet_site: str = FLEET_SITE_ID) -> str:
    """Crawlable main-content links to other fleet sites (excludes self)."""
    items = []
    for link in fleet_cross_link_items(fleet_site):
        href = link.href if link.href.endswith("/") else f"{link.href}/"
        about = f"{href}about.html"
        items.append(
            f'      <li><a href="{e(href)}">{e(link.label)}</a>'
            f' · <a href="{e(about)}">About</a></li>'
        )
    return f"""    <section class="about-section" aria-labelledby="about-network">
      <h2 id="about-network">Related sites</h2>
      <p>Also on this network:</p>
      <ul>
{chr(10).join(items)}
      </ul>
    </section>"""


def sitemap_lastmod(events: list[dict] | None = None, now: dt.datetime | None = None) -> str:
    """Newest published ``discovered_at`` from data (internal field), else build day.

    ``load_events()`` strips internal fields, so this reads ``data/events.json``
    directly for lastmod. The optional ``events`` arg is ignored for dates.
    """
    del events  # public rows have no discovered_at; use raw file
    dates: list[str] = []
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    for event in raw:
        if event.get("status") != "published":
            continue
        discovered = event.get("discovered_at")
        if isinstance(discovered, str) and len(discovered) >= 10:
            dates.append(discovered[:10])
    if dates:
        return max(dates)
    now = now or dt.datetime.now(MYT)
    return now.astimezone(MYT).date().isoformat()


def analytics_registry() -> AnalyticsRegistry:
    return load_analytics(ANALYTICS_CONFIG)


def render_analytics_loader(registry: AnalyticsRegistry | None = None) -> str:
    """Emit the shared kit analytics loader from ``data/analytics.json``."""
    return kit_render_analytics_loader(registry if registry is not None else analytics_registry())


def load_site(path: Path | None = None) -> dict[str, str]:
    """Load title/tagline/description/about_lead from data/site.json."""
    cfg = path or SITE_CONFIG
    if not cfg.is_file():
        raise SystemExit(f"missing site copy file: {cfg.relative_to(ROOT)}")
    payload = json.loads(cfg.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("data/site.json must be an object")
    site: dict[str, str] = {}
    for field in SITE_COPY_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"data/site.json is missing {field}")
        site[field] = value.strip()
    return site


def load_ga_measurement_id(path: Path | None = None) -> str:
    """GA4 measurement ID from data/site.json (kept in sync with analytics.json)."""
    raw = json.loads((path or SITE_CONFIG).read_text(encoding="utf-8")).get("ga4_measurement_id", "")
    if raw is None:
        raw = ""
    if not isinstance(raw, str):
        raise SystemExit("data/site.json ga4_measurement_id must be a string")
    value = raw.strip()
    if value and not GA_ID.fullmatch(value):
        raise SystemExit("data/site.json ga4_measurement_id must be empty or a GA4 measurement ID")
    return value


def assert_site_ga_matches_registry(registry: AnalyticsRegistry | None = None) -> str:
    """Require data/site.json ga4_measurement_id to match the analytics registry."""
    registry = registry if registry is not None else analytics_registry()
    site_id = load_ga_measurement_id()
    reg_id = registry.primary_ga4_id()
    if site_id != reg_id:
        raise SystemExit(
            "data/site.json ga4_measurement_id must match data/analytics.json "
            f"({site_id!r} != {reg_id!r})"
        )
    return reg_id


def load_events(path: Path = DATA) -> list[dict]:
    """Published events only, internal fields stripped. Fails on schema errors."""
    events = json.loads(path.read_text(encoding="utf-8"))
    errs = events_lib.validate_collection(events)
    if errs:
        raise SystemExit("Schema errors:\n" + "\n".join(errs))
    return events_lib.public(events)


def month_counts(events: list[dict]) -> dict[int, int]:
    counts = {m: 0 for m in range(1, 13)}
    for ev in events:
        counts[int(ev["month"])] += 1
    return counts


def default_month(now: dt.datetime | None = None) -> int:
    now = (now or dt.datetime.now(MYT)).astimezone(MYT)
    if now.year < YEAR:
        return 1
    if now.year > YEAR:
        return 12
    return now.month


def sort_key(ev: dict):
    # Undated events sink to the bottom of their month.
    return (ev.get("start_date") or "9999", ev["name"].lower())


def meta_date(ev: dict) -> tuple[str, str | None]:
    """Meta-row date text, plus the start date for <time>, or None when TBC.

    One day: ``15 OCT 2026``. Same month: ``2–4 OCT 2026``.
    Across months: ``22 JUL–16 AUG 2026``. ``date_tbc`` stays ``TBC``.
    """
    if ev.get("date_tbc") or not ev.get("start_date"):
        return "TBC", None
    s = dt.date.fromisoformat(ev["start_date"])
    f = dt.date.fromisoformat(ev["end_date"]) if ev.get("end_date") else None
    if not f or f == s:
        text = f"{s.day} {M[s.month - 1].upper()} {s.year}"
    elif f.year != s.year:
        text = (
            f"{s.day} {M[s.month - 1].upper()} {s.year}\u2013"
            f"{f.day} {M[f.month - 1].upper()} {f.year}"
        )
    elif f.month != s.month:
        text = (
            f"{s.day} {M[s.month - 1].upper()}\u2013"
            f"{f.day} {M[f.month - 1].upper()} {f.year}"
        )
    else:
        text = f"{s.day}\u2013{f.day} {M[s.month - 1].upper()} {s.year}"
    return text, s.isoformat()


def place_label(ev: dict) -> str:
    """Town when set, otherwise the division. One place label, never a source."""
    town = (ev.get("town") or "").strip()
    if town:
        return town
    return (ev.get("division") or "").strip()


def where(ev: dict) -> str:
    venue, town = ev.get("venue") or "", ev.get("town") or ""
    if not venue:
        return f"{town} (venue to be confirmed)" if town else "To be confirmed"
    return venue if town in venue else f"{venue}, {town}"


def card_destination(ev: dict) -> str | None:
    """Prefer the organiser page; fall back to a dedicated info article."""
    return ev.get("official_url") or ev.get("info_url") or None


def render_card(ev: dict) -> str:
    text, iso = meta_date(ev)
    if iso:
        when = f'<time datetime="{e(iso)}">{e(text)}</time>'
    else:
        when = f'<span class="event-when">{e(text)}</span>'
    place = place_label(ev)
    pill = (
        f'<span class="event-place"><span class="event-place-label">{e(place)}</span></span>'
        if place else ""
    )
    kind = (ev.get("event_type") or "").strip()
    kind_html = f'<span class="event-type">{e(kind)}</span>' if kind else ""
    dest = card_destination(ev)
    if dest:
        name = (
            f'<h3 class="event-name">'
            f'<a class="event-link" href="{e(dest)}" '
            f'target="_blank" rel="noopener noreferrer">{e(ev["name"])}</a></h3>'
        )
        interactive = f' tabindex="0" aria-label="Open event: {e(ev["name"])}"'
    else:
        name = f'<h3 class="event-name">{e(ev["name"])}</h3>'
        interactive = ""
    return f"""
      <li class="event-card" id="{e(ev['id'])}"{f' data-event-type="{e(kind)}"' if kind else ""}{interactive}>
        <p class="event-meta-row">
          {when}
          {pill}
          {kind_html}
        </p>
        {name}
        <p class="event-sum">{e(ev.get('summary') or '')}</p>
        <p class="event-venue"><span class="event-label">Venue</span> {e(where(ev))}</p>
      </li>"""


def render_tabs(counts: dict[int, int], current: int) -> str:
    out = []
    for m in range(1, 13):
        on = m == current
        n = counts[m]
        badge = f' <span class="category-filter-count" aria-hidden="true">{n}</span>' if n else ""
        out.append(
            f'<button type="button" role="tab" id="tab-{m}" aria-controls="panel-{m}" '
            f'class="category-filter-button{" is-active" if on else ""}" aria-selected="{str(on).lower()}" '
            f'tabindex="{0 if on else -1}" data-m="{m}" aria-label="{FULL[m-1]}, {n} event{"" if n == 1 else "s"}">'
            f'{M[m-1]}{badge}</button>')
    return " ".join(out)


def render_panels(events: list[dict], current: int) -> str:
    out = []
    for m in range(1, 13):
        items = sorted((x for x in events if int(x["month"]) == m), key=sort_key)
        body = "".join(render_card(x) for x in items) or \
            f'<li class="event-empty">No events listed for {FULL[m-1]} yet.</li>'
        hidden = "" if m == current else " hidden"
        out.append(f'<ol class="event-list" role="tabpanel" id="panel-{m}" aria-labelledby="tab-{m}" '
                   f'data-panel="{m}"{hidden}>{body}\n    </ol>')
    return "\n    ".join(out)


def canonical_url(page: str) -> str:
    if page == "home":
        return f"{SITE_ORIGIN}/"
    if page == "about":
        return f"{SITE_ORIGIN}/about.html"
    if page == "404":
        return f"{SITE_ORIGIN}/404.html"
    raise SystemExit(f"unknown page {page}")


def render_head(*, title: str, desc: str, canonical: str, site_name: str, analytics: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{desc}" />
  <meta name="robots" content="index,follow" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:site_name" content="{site_name}" />
  <meta property="og:url" content="{canonical}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{desc}" />
  <title>{title}</title>
  <script>
    document.documentElement.classList.add("js");
    const qsTheme = new URLSearchParams(location.search).get("theme");
    if (qsTheme) {{ try {{ localStorage.setItem("sarawak-theme", qsTheme); }} catch (e) {{}} }}
    try {{
      const storedTheme = localStorage.getItem("sarawak-theme");
      if (storedTheme === "dark" || (storedTheme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {{
        document.documentElement.dataset.theme = "dark";
      }}
    }} catch (error) {{}}
  </script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🗓️</text></svg>" />
  <link rel="preload" href="fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="stylesheet" href="style.css" />
  <link rel="stylesheet" href="events.css" />
  <script src="app.js" defer></script>
  <script src="events.js" defer></script>
  {analytics}
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>
"""


def shell(page: str, title: str, desc: str, main: str, site: dict[str, str] | None = None) -> str:
    site = load_site() if site is None else site
    registry = analytics_registry()
    assert_site_ga_matches_registry(registry)
    active = "home" if page == "home" else "about"
    brand = site["title"]
    header = kit_render_header(
        brand_title=brand,
        brand_href="./",
        active=active,
        nav_items=(
            NavItem("home", "./", "Home"),
            NavItem("about", "about.html", "About"),
        ),
    )
    footer = kit_render_footer(
        brand_title=brand,
        brand_note=FOOTER_NOTE,
        active=active,
        explore_items=(
            NavItem("home", "./", "Home"),
            NavItem("about", "about.html", "About"),
        ),
        credit_html=FOOTER_CREDIT,
        fleet_site="events",
        layout="column_stacks",
        fleet_section_label="Hub",
        extra_nav_right=FOOTER_CATEGORIES_INNER,
    )
    return (
        render_head(
            title=e(title),
            desc=e(desc),
            canonical=e(canonical_url(page)),
            site_name=e(brand),
            analytics=render_analytics_loader(registry),
        )
        + header
        + "\n"
        + main
        + footer
        + "\n"
        + render_back_to_top()
        + "\n</body>\n</html>\n"
    )

def updated_html(now: dt.datetime) -> str:
    d = now.astimezone(MYT)
    return (f'<p class="updated"><span class="updated-label">Last updated</span> '
            f'<time datetime="{d:%Y-%m-%d}">{d:%A, %d %b %Y}</time></p>').replace(d.strftime("%A, %d %b %Y"), d.strftime("%A, %d %b %Y").upper())


def render_index(events: list[dict], now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(MYT)
    site = load_site()
    cur = default_month(now)
    counts = month_counts(events)
    # Live home meta is description without its trailing period, plus ", listed by month."
    meta_desc = f"{site['description'].rstrip('.')}, listed by month."
    main = f"""  <main id="content">
    <header class="brief">
      <h1>{e(site["tagline"])}</h1>
      <p class="brief-deck">{e(site["description"])}</p>
      <p class="brief-about"><a href="about.html">About this listing</a></p>
      {updated_html(now)}
    </header>
    <section class="category-filter month-filter" aria-labelledby="month-filter-title">
      <p class="category-filter-title" id="month-filter-title">Browse by month</p>
      <div class="category-filter-scroll" data-category-scroll>
        <div class="category-filter-options" data-months role="tablist" aria-label="Months">{render_tabs(counts, cur)}</div>
      </div>
    </section>
    <h2 class="event-month-heading" data-month-heading>{FULL[cur-1]} {YEAR}</h2>
    {render_panels(events, cur)}
  </main>
"""
    return shell("home", "Events Sarawak", meta_desc, main, site)


def render_about(events: list[dict], now: dt.datetime | None = None, page: str = "about") -> str:
    site = load_site()
    about_meta = f"About {site['title']}, an independent listing of events across Sarawak."
    main = f"""  <main id="content">
    <header class="brief">
      <h1>About {e(site["title"])}</h1>
      <p class="brief-deck">{e(site["about_lead"])}</p>
    </header>
    <div class="event-list about-body">
      <p>{e(site["title"])} lists festivals, sports events, regattas, concerts and cultural celebrations happening around Sarawak, one month at a time. Each listing gives the date, the town (or the division when no town is set), the venue and a short factual description.</p>
      <p>When a date has not been fixed, the listing shows it as TBC.</p>
      <p><strong>{NOTE}</strong> Events can be moved, postponed or cancelled at short notice.</p>
      <p>This is an independent site and is not affiliated with the Sarawak Government.</p>
{render_fleet_network_section()}
    </div>
  </main>
"""
    return shell(page, "About · Events Sarawak", about_meta, main, site)


def render_robots() -> str:
    return f"User-agent: *\nAllow: /\nSitemap: {SITE_ORIGIN}/sitemap.xml\n"


def render_sitemap(events: list[dict] | None = None, now: dt.datetime | None = None) -> str:
    events = events if events is not None else load_events()
    lastmod = sitemap_lastmod(events, now)
    urls = (f"{SITE_ORIGIN}/", f"{SITE_ORIGIN}/about.html")
    entries = "\n".join(
        f"  <url>\n    <loc>{e(url)}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>"
        for url in urls
    )
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        f"{entries}\n"
        "</urlset>\n"
    )


def build(out: Path = DIST, now: dt.datetime | None = None) -> Path:
    events = load_events()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SITE, out)
    (out / "index.html").write_text(render_index(events, now), encoding="utf-8")
    (out / "about.html").write_text(render_about(events, now), encoding="utf-8")
    (out / "404.html").write_text(render_about(events, now, page="404"), encoding="utf-8")
    (out / "robots.txt").write_text(render_robots(), encoding="utf-8")
    (out / "sitemap.xml").write_text(render_sitemap(events, now), encoding="utf-8")
    (out / "CNAME").write_text((ROOT / "CNAME").read_text(encoding="utf-8"), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Built {build(Path(sys.argv[1]) if len(sys.argv) > 1 else DIST)}")
