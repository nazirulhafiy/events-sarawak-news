# Runbook: Maintainer Bot, events.sarawak.news

Maintainer Bot runs discovery and publishing for events.sarawak.news the same
way it does for ai.sarawak.news. Authoritative rules are in `docs/automation.md`,
and the record format is in `docs/schema.md`.

**Current state: preview only.** Live preview: https://events-sarawak-news.pages.dev/
(Cloudflare Pages project `events-sarawak-news`). Do not add DNS, a custom domain,
or a hub link, and do not go live without Nazirul's explicit yes.

## Cadence

- Daily at 07:00 Asia/Kuching, or when Nazirul asks.
- Weekly (Monday): also sweep for postponements and cancellations of events in the next 60 days.

## Each run

1. **Prepare.** Fetch `origin/main` of `nazirulhafiy/events-sarawak-news`. Generate `discovery_run_id` (for example `ev-2026-10-16`). Snapshot the private ledger (known URLs and outcomes).
2. **Launch one Cursor Cloud Agent** with `automation/prompts/daily-agent.md`, filling in:
   - `{{DISCOVERY_RUN_ID}}`
   - `{{PUBLICATION_MODE}}`: `pull_request` until a supervised run passes, then `direct_main` only with Nazirul's yes
   - `{{LEDGER_SNAPSHOT}}`
3. **Wait** for the terminal result (`published`, `no_update` or `blocked`).
4. **Confirm** the remote branch or PR state and the SHA yourself. Do not trust the agent's report alone.
5. **Ledger.** Write one record per screened URL: URL, canonical URL, first seen, last screened, run ID, outcome (`published`, `queued`, `duplicate`, `rejected`, `inaccessible`, `monitor`), one-line reason, agent run ID. The ledger is private and stays outside the repo.
6. **Redeploy the preview** after anything reaches `main` (below).
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

## Redeploying the preview

No CI deploy exists yet. Deploy `dist/` to the Cloudflare Pages project
`events-sarawak-news` (production branch `main`). It must stay on
`*.pages.dev` with no custom domain. Either:

- `npx wrangler pages deploy dist --project-name events-sarawak-news --branch main` (needs a Cloudflare API token with Pages:Edit), or
- what the preview currently uses: bundle `dist/` into one `_worker.js` that serves the files inline, and POST it as a multipart deployment (`manifest={}`, `branch=main`, `_worker.js`) to `/accounts/{id}/pages/projects/events-sarawak-news/deployments` through the Cloudflare API connector. The direct asset-upload endpoint returned "Authorization failed" from the connector.

After deploying, check that `https://events-sarawak-news.pages.dev/` returns 200 and the new event shows under its month.

## Hard stops

- Any test, validation, or build failure, or an unexpected diff, means `blocked`.
- A phone number, email or organiser contact anywhere in the data or on cards means `blocked`. Remove it, never publish it.
- Changes to docs, scripts, sources or CI in a content run mean `blocked`.
- DNS, domain, hub link, analytics or GA4 changes are out of scope. GA4 does not exist for this site yet.

## Screenshots

Use Playwright (`NODE_PATH=/home/box/repos/sifir-sprint/node_modules`): phone 390pt @3x cropped from just above the month tabs (at most 1.3:1), desktop 1440 @2x, light and dark.
