# events.sarawak.news: design

Status: **preview only**. Not live on events.sarawak.news, no DNS record, no CNAME, not linked from the sarawak.news hub. Pages carry `<meta name="robots" content="noindex">` until launch.

## Shell
Same template as ai.sarawak.news (`nazirulhafiy/sarawak-ai-news`) and bantuan.sarawak.news (`nazirulhafiy/bantuan-sarawak`):
- `site/style.css` and `site/app.js` are the shared shell (sticky bar, mobile nav, theme toggle, footer). Theme is stored in `localStorage["sarawak-theme"]`, falls back to `prefers-color-scheme`, and `?theme=light|dark` forces it.
- Font: Geist variable (`site/fonts/Geist-Variable.woff2`), self-hosted.
- Header brand "Events.Sarawak.News"; footer credits hafiy.my and states non-affiliation with the Sarawak Government.

## Page
- Brief: "Events in Sarawak, month by month." plus source line and last-updated date (build date, MYT).
- Month tabs (Jan to Dec, 2026) reuse the `.category-filter` pill style, and each tab carries a count badge. Months with no events get no badge.
- The current month in MYT (Asia/Kuching) is selected by default: build.py pre-selects the build-time month, and `events.js` re-selects using `Intl` with `timeZone: "Asia/Kuching"` on load. Before 2026 it shows January, and after 2026 it shows December. `?month=N` overrides.
- Note under the tabs: "Dates subject to change, check with organisers."
- No division filter. The division shows as a chip on each card.
- Card: date block, name, one-line summary, venue, organiser, contact (or "Organiser contact: to be confirmed"), division chip.
- Date block (approved smaller version): `#111111` background with brand yellow `#f7c948` text, 92px column (58px on phones). Ranges read `22–16` / `JUL–AUG`. Undated events show `TBC` and sort last in their month.
- All 12 month panels are pre-rendered as static HTML (ARIA tabs/tabpanels; arrow keys move between tabs), so the page works without JS.

## Build
- `python3 scripts/build.py` → `dist/` (index.html, about.html, 404.html, assets). Standard library only.
- `scripts/extract_calendar.py` is the extractor that regenerates `data/events-2026.json` from the official calendar PDF; `data/review.md` lists uncertain fields.
- Tests: `python3 -m unittest discover -s tests`.
- CI: `ci/build.yml` (move to `.github/workflows/build.yml`; the gh token on the box lacks `workflow` scope so it could not be pushed) (`build`) runs the tests, builds, and uploads a Pages artifact. **No deploy step during preview**, because GitHub Pages for nazirulhafiy resolves to hafiy.my/events-sarawak-news/.

## Hosting (preview)
Cloudflare Pages project `events-sarawak-news` (`*.pages.dev`), with no custom domain attached. At launch: attach events.sarawak.news, add DNS, remove `noindex`, link from the hub.

## Analytics
- Cloudflare Web Analytics beacon, token `092a061973fc4d899cd2e4b52952af89` (zone sarawak.news, shared sarawak.news site).
- **No GA4 yet**: no GA4 property exists for events.sarawak.news. Add the gtag snippet to `HEAD` in build.py once one is created.
