# events.sarawak.news: design

Status: **live** at https://events.sarawak.news. Hosted on GitHub Pages (custom domain `events.sarawak.news`, HTTPS). Pages are indexable (`index,follow`). Canonical URLs and the sitemap use `https://events.sarawak.news`. Not linked from the sarawak.news hub.

## Shell
Same template as ai.sarawak.news (`nazirulhafiy/sarawak-ai-news`) and bantuan.sarawak.news (`nazirulhafiy/bantuan-sarawak`):
- `site/style.css` and `site/app.js` are the shared shell (sticky bar, mobile nav, theme toggle, footer). Theme is stored in `localStorage["sarawak-theme"]`, falls back to `prefers-color-scheme`, and `?theme=light|dark` forces it.
- Font: Geist variable (`site/fonts/Geist-Variable.woff2`), self-hosted.
- Header brand "Events.Sarawak.News"; footer credits hafiy.my and states non-affiliation with the Sarawak Government.
- Footer nav matches the sarawak.news shell: **Explore** (Home, About) and **Categories** (Festival, Sports, Cultural, Concert). Category links go to `/?event_type=festival`, `sports`, `cultural`, or `concert`. On the home page, `events.js` hides cards that do not match the type, updates month tab count badges to the filtered totals, and switches to the first month that has a match when the current month has none. `?month=N` still selects the month tab; both query params can be combined.

## Page
- Brief: "Events in Sarawak, month by month." with the deck "Festivals, sports, cultural events and concerts across Sarawak." and the last-updated date (build date, MYT). There is no source attribution anywhere on the site (cards, about, footer, meta). The 2026 tourism calendar was only the starter seed.
- Month tabs (Jan to Dec, 2026) reuse the `.category-filter` pill style, and each tab carries a count badge. Months with no events get no badge. The "Browse by month" label stays all-caps. The shared shell sets that label at 10px, weight 850, muted grey. On this page it is 13px, weight 900, body ink (`var(--ink)`), with 12px of space before the pills.
- The current month in MYT (Asia/Kuching) is selected by default: build.py pre-selects the build-time month, and `events.js` re-selects using `Intl` with `timeZone: "Asia/Kuching"` on load. Before 2026 it shows January, and after 2026 it shows December. `?month=N` overrides.
- No division filter.
- Card: meta row, name, 1-2 sentence summary, venue (or "{town} (venue to be confirmed)"), and an "Official site" link when `official_url` is set. **No organiser or contact lines, no phone numbers, and no source attribution**: those stay off the card.
- Card type matches ai.sarawak.news story cards. The name (`.event-name`, same role as `.story-card h2`) is 17px, weight 800, line-height 1.35, letter-spacing -0.012em, at every breakpoint. The summary (`.event-sum`, same role as `.story-summary`) is 13px, line-height 1.55, colour `var(--muted)`.
- Hover matches `.story-card:hover`, and only when `official_url` is set. The "Official site" link stretches across the card, so the card opens that URL. On a device that can hover, the border becomes `#cbd1da` (dark theme `#4b5663`), the shadow is `0 8px 20px`, and the card lifts `translateY(-3px)` with a 0.25deg tilt (the opposite way on even cards). The news hover does not change the fill; the background stays `var(--card)`. Keyboard focus on that link uses the same yellow outline as `.story-card:focus-visible`. A card with no official URL is not a control: no pointer, no border change, no lift. `prefers-reduced-motion: reduce` drops the lift.
- Meta row, above the title, same inline pattern as ai.sarawak.news `.story-meta-row` (date, then labels). There is no left-hand date square and no story rank number. On the news row, yellow `.story-source-label` is the story source and red `.story-section` is the story topic (`color: var(--sarawak-red-ink)`, weight 900, no fill). Events do not print the news source or topic. The yellow label is the **place**: town when set, otherwise division. The red label is `event_type` (`festival`, `sports`, `concert`, `cultural`), same red text and no fill. Races use `sports`. Every published regatta uses `festival` for now. It is omitted when `event_type` is empty. The published listing sets a type on every event, so every published card shows the red label.
- Date text is uppercase: `15 OCT 2026`. A range in one month reads `2–4 OCT 2026`. A range across months reads `22 JUL–16 AUG 2026`. Events with `date_tbc: true` show `TBC` and sort last in their month.
- All 12 month panels are pre-rendered as static HTML (ARIA tabs/tabpanels; arrow keys move between tabs), so the page works without JS.

## Build
- `python3 scripts/build.py` → `dist/` (index.html, about.html, 404.html, assets). Standard library only.
- Data: `data/events.json` in the standard schema (`docs/schema.md`). Only `published` records render, and internal fields (`source_url`, `source_name`, `discovered_at`, `status`, `review_note`) never do. Discovery and publishing: `docs/automation.md`, with the Maintainer Bot runbook in `docs/runbook.md`.
- Tests: `python3 -m unittest discover -s tests`.
- CI: `.github/workflows/build.yml` and `.github/workflows/discover.yml`. `build.yml` runs tests, `scripts/validate.py`, `scripts/build.py`, uploads `dist/` as a Pages artifact, and on push to `main` deploys via `actions/deploy-pages@v4` to the `github-pages` environment.
- Production origin: `https://events.sarawak.news`. The build writes `robots.txt` (`Allow: /` and `Sitemap: https://events.sarawak.news/sitemap.xml`) and `sitemap.xml` for the home page and `about.html`. Every HTML page has `<meta name="robots" content="index,follow">` and a `<link rel="canonical">` on that origin (`/`, `/about.html`, `/404.html`). `404.html` is not in the sitemap.

## Hosting
GitHub Pages from `nazirulhafiy/events-sarawak-news` (`main`), deployed by `.github/workflows/build.yml`. Custom domain `events.sarawak.news` with HTTPS (GitHub-managed certificate). `scripts/build.py` writes `dist/CNAME` from the repo root `CNAME` file. Do not attach any other domain. A hub link still needs Nazirul's explicit approval.

## Analytics
- Cloudflare Web Analytics beacon, token `092a061973fc4d899cd2e4b52952af89` (zone sarawak.news, shared sarawak.news site). The beacon is on every page.
- GA4 property **Sarawak Events**. The measurement ID is the only value in `data/site.json`, key `ga4_measurement_id`, currently `G-P7Y5Z19Q46`. When that field is set, `scripts/build.py` injects the gtag snippet in `HEAD`. When it is empty, built pages include neither `gtag` nor `googletagmanager`.
