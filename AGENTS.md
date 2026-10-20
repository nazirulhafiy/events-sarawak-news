# AGENTS.md

## Project
This repo is a dependency-free static site listing events across
Sarawak by month. **Live**: https://events.sarawak.news
(GitHub Pages via `.github/workflows/build.yml` on `nazirulhafiy/events-sarawak-news`).
No further DNS, custom domain or hub link without Nazirul's explicit approval.

- `data/site.json`: site `title`, `tagline`, `description`, `about_lead`, and GA4 id (single source of truth for public wording; GA4 must match `data/analytics.json`).
- `data/analytics.json`: kit-shaped analytics registry (`sn_internal`, hosts, GA4, CF token).
- `kit/`: vendored sarawak.news shared kit (pinned by `kit/PIN` to a hub commit). See `kit/README.md`.
- `data/events.json`: published events (schema: `docs/schema.md`).
- `data/review-queue.json`: candidates awaiting review.
- `data/sources.json`: public source pages watched for discovery.
- `scripts/events_lib.py`: schema validation, normalisation and dedupe.
- `scripts/discover.py`, `scripts/queue.py`, `scripts/publish.py`, `scripts/validate.py`: the pipeline (`docs/automation.md`).
- `scripts/build.py`: renders `dist/` (imports fleet chrome from `kit/`).
- `site/`: shared sarawak.news shell assets plus `events.css`/`events.js`.
- `.github/workflows/`: GitHub Actions workflows (`build.yml`, `discover.yml`).

## Rules
- No phone numbers, emails or organiser contact lines anywhere: not in the data, not on cards.
- No on-site source attribution. `source_url` and `source_name` are internal.
- Summaries are 1-2 short factual sentences in original wording.
- Oct–Dec 2026 published events need a card link: prefer `official_url`, else `info_url` (news or official social). Enforced by `scripts/validate.py` / `events_lib`. No `intourcams.my` URLs. Weekly Monday scan adds sourced events for present/future dates (`docs/runbook.md`).
- Design or behaviour changes update `docs/design.md` in the same change.
- Content runs follow `docs/automation.md`, and Maintainer Bot follows `docs/runbook.md`.

## Required checks
```bash
python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"   # CI clones hub at kit/PIN
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

When opening the **live** site, use `?internal=1` so `sn_internal` marks GA4 internal and skips the Cloudflare beacon.
