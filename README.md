# events-sarawak-news

Preview of **events.sarawak.news**: events across Sarawak, month by month. Not live and no custom domain. Preview: https://events-sarawak-news.pages.dev/

Published events: 114 (content audit 2026-10-15).

```
python3 scripts/validate.py              # schema check
python3 -m unittest discover -s tests    # tests
python3 scripts/build.py                 # -> dist/
python3 scripts/discover.py              # candidate leads -> dist/candidate-urls.json
python3 scripts/queue.py manifest.json   # -> data/review-queue.json
python3 scripts/publish.py               # approved -> data/events.json, rebuild
```

Docs: `docs/schema.md` (event schema), `docs/automation.md` (discovery/publish contract), `docs/runbook.md` (Maintainer Bot), `docs/design.md`.
