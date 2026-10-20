# events-sarawak-news

<!-- BEGIN GENERATED: site-copy -->
| Field | Value |
| --- | --- |
| `title` | Events.Sarawak.News |
| `tagline` | Events in Sarawak, month by month. |
| `description` | Festivals, sports, cultural events and concerts across Sarawak. |
<!-- END GENERATED: site-copy -->

**events.sarawak.news** — site title, tagline, description, and About lead live in `data/site.json`. Live: https://events.sarawak.news.

<!-- BEGIN GENERATED: hosting -->
| Field | Value |
| --- | --- |
| `hostname` | `events.sarawak.news` |
| `target` | GitHub Pages |
<!-- END GENERATED: hosting -->

Hosted on **GitHub Pages** from `nazirulhafiy/events-sarawak-news` (`main`). Production deploys via `.github/workflows/build.yml` (`actions/deploy-pages@v4` to the `github-pages` environment). Migrated from Cloudflare Pages on **15 October 2026** (no `wrangler pages deploy`).

Published events: 106 (content audit 2026-10-19).

```
python3 scripts/validate.py              # schema check
python3 -m unittest discover -s tests    # tests
python3 scripts/build.py                 # -> dist/
python3 kit/generate_docs.py --check     # generated fact blocks
python3 scripts/discover.py              # candidate leads -> dist/candidate-urls.json
python3 scripts/queue.py manifest.json   # -> data/review-queue.json
python3 scripts/publish.py               # approved -> data/events.json, rebuild
```

<!-- BEGIN GENERATED: analytics -->
| Field | Value |
| --- | --- |
| `ga4_measurement_id` | `G-P7Y5Z19Q46` |
| `cf_beacon_token` | `092a061973fc4d899cd2e4b52952af89` |
| `internal_cookie` | `sn_internal` |
| `hosts` | `events.sarawak.news`, `www.events.sarawak.news` |
<!-- END GENERATED: analytics -->

Docs: `docs/schema.md` (event schema), `docs/automation.md` (discovery/publish contract), `docs/runbook.md` (Maintainer Bot), `docs/design.md`, `docs/operations.md` (hosting, deploy, analytics), `docs/ci.md` (PR docs check).
