# Runbook: Maintainer Bot, events.sarawak.news

Maintainer Bot runs discovery and publishing for events.sarawak.news the same
way it does for ai.sarawak.news. Authoritative rules are in `docs/automation.md`,
and the record format is in `docs/schema.md`.

**Current state: live** at https://events.sarawak.news
(GitHub Pages from `nazirulhafiy/events-sarawak-news`, custom domain with HTTPS).
Do not attach any other domain, and do not add a hub link, without Nazirul's explicit yes.

## Cadence

- Daily at 07:00 Asia/Kuching (`discover.yml` leads + Maintainer Bot), or when Nazirul asks.
- Weekly (Monday): also sweep for postponements and cancellations of events in the next 60 days, **and** scan for new events relevant to the period of the scan — **present time and future** (past-only backfill is not the default). Add only when a verifiable `official_url` or `info_url` exists; see source-link rule in `docs/schema.md`.

## Each run

1. **Prepare.** Fetch `origin/main` of `nazirulhafiy/events-sarawak-news`. Generate `discovery_run_id` (for example `ev-2026-10-16`). Snapshot the private ledger (known URLs and outcomes).
2. **Launch one Cursor Cloud Agent** with `automation/prompts/daily-agent.md`, filling in:
   - `{{DISCOVERY_RUN_ID}}`
   - `{{PUBLICATION_MODE}}`: `pull_request` until a supervised run passes, then `direct_main` only with Nazirul's yes
   - `{{LEDGER_SNAPSHOT}}`
3. **Wait** for the terminal result (`published`, `no_update` or `blocked`).
4. **Confirm** the remote branch or PR state and the SHA yourself. Do not trust the agent's report alone.
5. **Ledger.** Write one record per screened URL: URL, canonical URL, first seen, last screened, run ID, outcome (`published`, `queued`, `duplicate`, `rejected`, `inaccessible`, `monitor`), one-line reason, agent run ID. The ledger is private and stays outside the repo.
6. **Deploy** happens automatically when changes reach `main` (below). On `published`, confirm the live site after the `build` workflow finishes.
7. **Report** to Nazirul only on `PR-ready`, `published` or `blocked`. Stay quiet on `no_update`. Include **Needs manual check** items.

## Commands (what the Cloud Agent runs)

```bash
python3 scripts/discover.py --limit-per-source 8      # leads -> dist/candidate-urls.json
# verify each lead in a browser, write manifest.json (automation/candidate.schema.json)
python3 scripts/queue.py manifest.json                # -> data/review-queue.json (pending / duplicate)
python3 scripts/publish.py --approve <id> [--approve <id>]
python3 scripts/publish.py --reject <id> --reason "not in Sarawak"
python3 scripts/publish.py                            # approved -> data/events.json, rebuild dist/
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

Postponed: edit dates in `data/events.json` and add a `review_note`. Cancelled: set `status` to `cancelled`; it stops rendering.

**Oct–Dec 2026 source-link policy:** before leaving an event `published` with `start_date` in October–December 2026, confirm it has `official_url` and/or `info_url` (official site, social, or news). If neither can be verified, cancel it — do not invent a URL. Full rule: `docs/schema.md` (Hard rules). New finds come from the Monday weekly scan (present + future), not past-only backfill.

## Production deploy (GitHub Pages)

The `.github/workflows/build.yml` workflow runs on every push to `main` and on pull requests:

1. **test-build** — unit tests, `scripts/validate.py`, `scripts/build.py`, then uploads `dist/` as a GitHub Pages artifact (including `dist/CNAME` for `events.sarawak.news`).
2. **deploy** (push to `main` only) — publishes that artifact to the `github-pages` environment via `actions/deploy-pages@v4`.

Repository **Settings → Pages** should use **GitHub Actions** as the source. The custom domain `events.sarawak.news` is declared in the built `CNAME` file; DNS must point at GitHub Pages. HTTPS is enforced by GitHub once the domain is verified.

After a merge to `main`, open the latest `build` workflow run and confirm **deploy** succeeded, then check that `https://events.sarawak.news/` returns 200 and the new event shows under its month.

## Hard stops

- Any test, validation, or build failure, or an unexpected diff, means `blocked`.
- A phone number, email or organiser contact anywhere in the data or on cards means `blocked`. Remove it, never publish it.
- Changes to docs, scripts, sources or CI in a content run mean `blocked`.
- DNS, domain, hub link, or analytics changes are out of scope for a content run. GA4 is already configured in `data/site.json`.

## Screenshots

Use Playwright (`NODE_PATH=/home/box/repos/sifir-sprint/node_modules`): phone 390pt @3x cropped from just above the month tabs (at most 1.3:1), desktop 1440 @2x, light and dark.
