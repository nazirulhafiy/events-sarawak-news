"""Add a verified candidate manifest to data/review-queue.json.

Validates the manifest shape, normalises each candidate to the event schema
(status 'pending'), and marks duplicates of published or queued events as
status 'duplicate' instead of adding a second record.

    python3 scripts/queue.py path/to/manifest.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import events_lib as L  # noqa: E402

MANIFEST_REQUIRED = ["name", "start_date", "month", "town", "division", "summary", "url", "source",
                     "language_verified", "discovered_at", "source_checked_at", "discovery_source_url"]


def check_manifest(m: dict) -> list[str]:
    errs = []
    for k in ("schema_version", "run_id", "generated_at", "timezone", "candidates"):
        if k not in m:
            errs.append(f"manifest missing '{k}'")
    if errs:
        return errs
    if m["schema_version"] != 1 or m["timezone"] != "Asia/Kuching" or not m["candidates"]:
        errs.append("manifest needs schema_version 1, timezone Asia/Kuching and at least one candidate")
    for i, c in enumerate(m["candidates"]):
        for k in MANIFEST_REQUIRED:
            if k not in c:
                errs.append(f"candidate {i}: missing '{k}'")
        if c.get("language_verified") is not True:
            errs.append(f"candidate {i}: language_verified must be true")
    return errs


def enqueue(manifest: dict, events: list[dict], queue: list[dict]) -> tuple[list[dict], dict]:
    errs = check_manifest(manifest)
    if errs:
        raise ValueError("\n".join(errs))
    report = {"pending": [], "duplicate": [], "invalid": []}
    for c in manifest["candidates"]:
        ev = L.normalise_candidate(c)
        problems = L.validate_event(ev)
        if problems:
            report["invalid"].append({"name": c.get("name"), "problems": problems})
            continue
        dup = L.find_duplicate(ev, events + [q for q in queue if q["status"] in ("pending", "approved")])
        if dup:
            report["duplicate"].append({"id": ev["id"], "of": dup["id"]})
            continue
        queue.append(ev)
        report["pending"].append(ev["id"])
    return queue, report


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__); return 2
    manifest = json.loads(Path(argv[0]).read_text())
    queue, report = enqueue(manifest, L.load(L.EVENTS), L.load(L.QUEUE))
    L.save(L.QUEUE, queue)
    print(json.dumps(report, indent=2))
    return 1 if report["invalid"] else 0


if __name__ == "__main__":
    sys.exit(main())
