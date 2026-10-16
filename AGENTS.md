# AGENTS.md

## Project
Events.Sarawak.News is a dependency-free static site listing events across
Sarawak by month. **Live**: https://events.sarawak.news
(Cloudflare Pages project `events-sarawak-news`; `*.pages.dev` remains the project subdomain).
No further DNS, custom domain or hub link without Nazirul's explicit approval.

- `data/events.json`: published events (schema: `docs/schema.md`).
- `data/review-queue.json`: candidates awaiting review.
- `data/sources.json`: public source pages watched for discovery.
- `scripts/events_lib.py`: schema validation, normalisation and dedupe.
- `scripts/discover.py`, `scripts/queue.py`, `scripts/publish.py`, `scripts/validate.py`: the pipeline (`docs/automation.md`).
- `scripts/build.py`: renders `dist/`.
- `site/`: shared sarawak.news shell assets plus `events.css`/`events.js`.
- `.github/workflows/`: GitHub Actions workflows (`build.yml`, `discover.yml`).

## Rules
- No phone numbers, emails or organiser contact lines anywhere: not in the data, not on cards.
- No on-site source attribution. `source_url` and `source_name` are internal.
- Summaries are 1-2 short factual sentences in original wording.
- Oct–Dec 2026 published events need `official_url` or `info_url` (official / social / news); otherwise cancel — see `docs/schema.md`.
- Design or behaviour changes update `docs/design.md` in the same change.
- Content runs follow `docs/automation.md`, and Maintainer Bot follows `docs/runbook.md`.

## Required checks
```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```
