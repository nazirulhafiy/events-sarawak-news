# events-sarawak-news

**events.sarawak.news** — site title, tagline, description, and About lead live in `data/site.json`. Live: https://events.sarawak.news.

Hosted on **GitHub Pages** from `nazirulhafiy/events-sarawak-news` (`main`). Production deploys via `.github/workflows/build.yml` (`actions/deploy-pages@v4` to the `github-pages` environment). Migrated from Cloudflare Pages on **15 October 2026** (no `wrangler pages deploy`).

Published events: 106 (content audit 2026-10-19).

```
python3 scripts/validate.py              # schema check
python3 -m unittest discover -s tests    # tests
python3 scripts/build.py                 # -> dist/
python3 scripts/discover.py              # candidate leads -> dist/candidate-urls.json
python3 scripts/queue.py manifest.json   # -> data/review-queue.json
python3 scripts/publish.py               # approved -> data/events.json, rebuild
```

Docs: `docs/schema.md` (event schema), `docs/automation.md` (discovery/publish contract), `docs/runbook.md` (Maintainer Bot), `docs/design.md`, `docs/operations.md` (hosting, deploy, analytics).
