# Operations: events.sarawak.news

Production site: https://events.sarawak.news  
Repository: `nazirulhafiy/events-sarawak-news`  
Site wording (`title`, `tagline`, `description`, `about_lead`): `data/site.json` (single source; do not hand-type elsewhere).

## Hosting and deploy

| Item | Value |
|------|--------|
| Platform | GitHub Pages (custom domain `events.sarawak.news`, HTTPS) |
| Source branch | `main` |
| Workflow | `.github/workflows/build.yml` |
| Pages source (repo settings) | **GitHub Actions** |
| `CNAME` | Repo root `CNAME` → copied to `dist/CNAME` by `scripts/build.py` |

**Migration (15 October 2026):** production moved from Cloudflare Pages (`events-sarawak-news` project) to GitHub Pages. Deploy is CI-only via GitHub Actions; there is no `wrangler pages deploy` or `*.pages.dev` preview for this site.

### `build.yml` jobs

1. **test-build** (every push and PR) — `python3 kit/sync.py --check` (shallow-fetches hub at `kit/PIN`), `python -m unittest discover -s tests`, `scripts/validate.py`, `scripts/build.py`, then `actions/upload-pages-artifact@v3` with `path: dist`.
2. **deploy** (push to `main` only) — `actions/deploy-pages@v4` to the `github-pages` environment after **test-build** succeeds.

After merge to `main`, confirm the **deploy** job in the latest **build** workflow run, then spot-check https://events.sarawak.news/.

Discovery scheduling is separate: `.github/workflows/discover.yml` (artifact only; no publish).

Maintainer Bot cadence and publishing steps: `docs/runbook.md`. Data contract: `docs/automation.md`.

## Analytics

`scripts/build.py` injects the shared kit analytics loader (from `data/analytics.json`) on every HTML page. Beacons load only on production hostnames.

| Service | ID / token | Notes |
|---------|------------|--------|
| Google Analytics 4 | `G-P7Y5Z19Q46` | Property **Sarawak Events**; registry + `data/site.json` → `ga4_measurement_id` (must match) |
| Cloudflare Web Analytics | `092a061973fc4d899cd2e4b52952af89` | Zone `sarawak.news`, shared with other sarawak.news sites |
| Internal cookie | `sn_internal` | `?internal=1` / `?internal=0`; skips CF beacon and marks GA4 internal |

Analytics or domain changes are out of scope for routine content runs (`docs/runbook.md`).

## Local build

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -m http.server 4173 -d dist
```
