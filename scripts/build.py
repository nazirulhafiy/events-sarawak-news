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
DATA = ROOT / "data" / "events.json"
SITE_CONFIG = ROOT / "data" / "site.json"
SITE = ROOT / "site"
DIST = ROOT / "dist"
MYT = dt.timezone(dt.timedelta(hours=8))
YEAR = 2026
SITE_ORIGIN = "https://events.sarawak.news"
CF_TOKEN = "092a061973fc4d899cd2e4b52952af89"  # zone sarawak.news, shared site
GA_ID = re.compile(r"G-[A-Z0-9]+\Z")
M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FULL = ["January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"]
NOTE = "Dates subject to change, check with organisers."
e = html.escape


def load_ga_measurement_id(path: Path | None = None) -> str:
    """GA4 measurement ID from data/site.json. Blank means omit gtag."""
    raw = json.loads((path or SITE_CONFIG).read_text(encoding="utf-8")).get("ga4_measurement_id", "")
    if raw is None:
        raw = ""
    if not isinstance(raw, str):
        raise SystemExit("data/site.json ga4_measurement_id must be a string")
    value = raw.strip()
    if value and not GA_ID.fullmatch(value):
        raise SystemExit("data/site.json ga4_measurement_id must be empty or a GA4 measurement ID")
    return value


def render_ga_script(measurement_id: str) -> str:
    if not measurement_id:
        return ""
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>\n'
        "  <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
        f"gtag('js',new Date());gtag('config','{measurement_id}');</script>"
    )


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


HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{desc}" />
  <meta name="robots" content="index,follow" />
  <link rel="canonical" href="{canonical}" />
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
  <!-- Cloudflare Web Analytics (zone sarawak.news) -->
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "{cf}"}}'></script>
  {ga}
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>
  <header class="bar">
    <div class="bar-inner">
      <span class="brand-lockup"><a class="brand" href="./"><img class="brand-mark brand-mark-light" src="icons/nav-mark-transparent.svg" alt="" width="220" height="220" decoding="async" aria-hidden="true" /><img class="brand-mark brand-mark-dark" src="icons/nav-mark-transparent-dark.svg" alt="" width="220" height="220" decoding="async" aria-hidden="true" /><span class="brand-text">Events.Sarawak.News</span></a></span>
      <nav class="site-nav" id="primary-navigation" aria-label="Primary">
        <a class="site-nav-link{home_on}" href="./"{home_cur}>Home</a>
        <a class="site-nav-link{about_on}" href="about.html"{about_cur}>About</a>
      </nav>
      <span class="bar-rule-tail" aria-hidden="true"></span>
      <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-navigation" aria-label="Open navigation" title="Open navigation">
        <span></span><span></span><span></span>
      </button>
      <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
        <svg class="theme-icon-morph" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24">
          <mask id="theme-toggle-moon-mask"><rect width="24" height="24" fill="#fff"></rect><circle cx="17" cy="7" r="7" fill="#000"></circle></mask>
          <circle class="theme-icon-moon" cx="12" cy="12" r="9" mask="url(#theme-toggle-moon-mask)"></circle>
          <circle class="theme-icon-sun" cx="12" cy="12" r="5"></circle>
          <g class="theme-icon-rays">
            <line x1="12" y1="1.6" x2="12" y2="3.8"></line><line x1="12" y1="20.2" x2="12" y2="22.4"></line>
            <line x1="1.6" y1="12" x2="3.8" y2="12"></line><line x1="20.2" y1="12" x2="22.4" y2="12"></line>
            <line x1="4.6" y1="4.6" x2="6.2" y2="6.2"></line><line x1="17.8" y1="17.8" x2="19.4" y2="19.4"></line>
            <line x1="4.6" y1="19.4" x2="6.2" y2="17.8"></line><line x1="17.8" y1="6.2" x2="19.4" y2="4.6"></line>
          </g>
        </svg>
      </button>
    </div>
  </header>
"""

FOOT = """  <footer class="site-footer">
    <div class="site-footer-main">
      <div class="site-footer-summary">
        <p class="site-footer-brand">Events.Sarawak.News</p>
        <p class="site-footer-note">An independent listing of events across Sarawak.</p>
      </div>
      <nav aria-label="Explore" class="site-footer-nav">
        <h2>Explore</h2>
        <ul>
          <li><a class="site-footer-link" href="./"{home_cur}>Home</a></li>
          <li><a class="site-footer-link" href="about.html"{about_cur}>About</a></li>
          <li><a class="site-footer-link" href="mailto:contact@sarawak.news">Contact</a></li>
        </ul>
        <h2 class="site-footer-categories-title">Categories</h2>
        <ul>
          <li><a class="site-footer-link" href="/?event_type=festival">Festival</a></li>
          <li><a class="site-footer-link" href="/?event_type=sports">Sports</a></li>
          <li><a class="site-footer-link" href="/?event_type=cultural">Cultural</a></li>
          <li><a class="site-footer-link" href="/?event_type=concert">Concert</a></li>
        </ul>
      </nav>
    </div>
    <div class="site-footer-bottom">
      <p>Built by <a class="site-footer-link site-footer-credit-link" href="https://hafiy.my" target="_blank" rel="noopener noreferrer">hafiy.my</a>, an independent publication. Not affiliated with the Sarawak Government.</p>
    </div>
  </footer>
</body>
</html>
"""


def canonical_url(page: str) -> str:
    if page == "home":
        return f"{SITE_ORIGIN}/"
    if page == "about":
        return f"{SITE_ORIGIN}/about.html"
    if page == "404":
        return f"{SITE_ORIGIN}/404.html"
    raise SystemExit(f"unknown page {page}")


def shell(page: str, title: str, desc: str, main: str) -> str:
    home = page == "home"
    kw = dict(home_on=" is-active" if home else "", about_on="" if home else " is-active",
              home_cur=' aria-current="page"' if home else "",
              about_cur="" if home else ' aria-current="page"')
    return (HEAD.format(title=e(title), desc=e(desc), cf=CF_TOKEN,
                       canonical=e(canonical_url(page)),
                       ga=render_ga_script(load_ga_measurement_id()), **kw)
            + main
            + FOOT.format(home_cur=kw["home_cur"], about_cur=kw["about_cur"]))


def updated_html(now: dt.datetime) -> str:
    d = now.astimezone(MYT)
    return (f'<p class="updated"><span class="updated-label">Last updated</span> '
            f'<time datetime="{d:%Y-%m-%d}">{d:%A, %d %b %Y}</time></p>').replace(d.strftime("%A, %d %b %Y"), d.strftime("%A, %d %b %Y").upper())


def render_index(events: list[dict], now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(MYT)
    cur = default_month(now)
    counts = month_counts(events)
    main = f"""  <main id="content">
    <header class="brief">
      <h1>Events in Sarawak, month by month.</h1>
      <p class="brief-deck">Festivals, sports, cultural events and concerts across Sarawak.</p>
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
    return shell("home", "Events Sarawak", "Festivals, sports, cultural events and concerts across Sarawak, listed by month.", main)


def render_about(events: list[dict], now: dt.datetime | None = None, page: str = "about") -> str:
    main = f"""  <main id="content">
    <header class="brief">
      <h1>About Events.Sarawak.News</h1>
      <p class="brief-deck">A plain month-by-month listing of events across Sarawak.</p>
    </header>
    <div class="event-list about-body">
      <p>Events.Sarawak.News lists festivals, sports events, regattas, concerts and cultural celebrations happening around Sarawak, one month at a time. Each listing gives the date, the town (or the division when no town is set), the venue and a short factual description.</p>
      <p>When a date has not been fixed, the listing shows it as TBC.</p>
      <p><strong>{NOTE}</strong> Events can be moved, postponed or cancelled at short notice.</p>
      <p>This is an independent site and is not affiliated with the Sarawak Government.</p>
    </div>
  </main>
"""
    return shell(page, "About · Events Sarawak", "About Events.Sarawak.News, an independent listing of events across Sarawak.", main)


def render_robots() -> str:
    return f"User-agent: *\nAllow: /\nSitemap: {SITE_ORIGIN}/sitemap.xml\n"


def render_sitemap(now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(MYT)
    lastmod = now.astimezone(MYT).date().isoformat()
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
    (out / "sitemap.xml").write_text(render_sitemap(now), encoding="utf-8")
    (out / "CNAME").write_text((ROOT / "CNAME").read_text(encoding="utf-8"), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Built {build(Path(sys.argv[1]) if len(sys.argv) > 1 else DIST)}")
