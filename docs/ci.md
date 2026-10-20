# Continuous integration

## Build workflow

The **build** workflow (`.github/workflows/build.yml`) shallow-fetches
`nazirulhafiy/sarawak-news-hub` at the SHA in `kit/PIN`, runs
`python3 kit/sync.py --check`, then `python3 kit/generate_docs.py --check`,
unit tests, schema validation, a static build, and (on `main` pushes) GitHub
Pages deploy.

Local kit edits, a stale pin, or drifted generated fact blocks fail the job.

### Concurrency

- **Pull requests:** `test-build` uses a per-PR concurrency group with
  `cancel-in-progress`, so new commits on the same PR cancel an older run on
  that PR only. Different PRs do not cancel each other.
- **`main` pushes and deploy:** share a `pages` group with
  `cancel-in-progress: false`, so a Pages deploy is never cancelled mid-flight.

## Docs check (prose)

Pull requests run the **docs check** workflow
(`.github/workflows/docs-check.yml`) on `opened`, `synchronize`, `reopened`,
`labeled`, and `unlabeled` events.

The check watches only design and behaviour sources, not editorial event data:

- `site/**/*.css`
- `site/**/*.js`
- `site/fonts/**`
- `kit/**` (shared Sarawak News kit)
- `scripts/build.py` (HTML page structure and markup are templated here)
- `scripts/docs_check_pr.py`
- `data/site.json` (site title, tagline, description, and About lead)
- `data/analytics.json` (GA4 / CF registry)

It does **not** watch other `data/` files (such as `events.json`), generated
`dist/` output, or discovery pipeline scripts, so content runs are not blocked
by this gate.

### Pass and fail

- If the pull request changes any watched file **and** changes nothing under
  `docs/`, the check fails with a message to update `docs/design.md` (or
  another doc under `docs/`) or to add the `no-docs-needed` label.
- If the pull request includes changes under `docs/`, the check passes.
- If the pull request has the `no-docs-needed` label, the check passes even
  when watched files change without `docs/` updates.

The workflow creates the `no-docs-needed` label in the repository when it is
missing.

Logic lives in `scripts/docs_check_pr.py` for local debugging:

```bash
DOCS_CHECK_BASE=origin/main DOCS_CHECK_HEAD=HEAD python3 scripts/docs_check_pr.py
```

Set `GITHUB_EVENT_PATH` to a saved pull-request event JSON when testing label
bypass locally.

## Generated docs (kit)

`python3 kit/generate_docs.py --check` is a separate gate. It compares the
interiors of `<!-- BEGIN GENERATED: … -->` blocks in `docs/design.md` and
`README.md` to fresh renders from `data/site.json`, `data/analytics.json`,
`CNAME`, and `site/style.css`. It does not replace the prose docs check.
