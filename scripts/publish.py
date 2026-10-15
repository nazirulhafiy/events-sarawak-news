"""Publish reviewed queue entries into data/events.json, then rebuild.

    python3 scripts/publish.py --approve ID [--approve ID ...]   # pending -> approved
    python3 scripts/publish.py --reject ID --reason "..."         # pending -> rejected
    python3 scripts/publish.py                                    # move all approved -> published, rebuild

Published records keep their internal fields (source_url, discovered_at,
status, review_note) in data/events.json; build.py never renders them.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import events_lib as L  # noqa: E402


def set_status(queue: list[dict], ids: list[str], status: str, reason: str | None = None) -> None:
    by = {q["id"]: q for q in queue}
    for i in ids:
        if i not in by:
            raise SystemExit(f"{i}: not in review queue")
        by[i]["status"] = status
        if reason:
            by[i]["review_note"] = reason


def publish(events: list[dict], queue: list[dict]) -> tuple[list[dict], list[dict], list[str]]:
    moved, rest = [], []
    for q in queue:
        if q["status"] == "approved":
            if L.find_duplicate(q, events):
                q["status"] = "duplicate"; rest.append(q); continue
            moved.append(dict(q, status="published"))
        else:
            rest.append(q)
    new = events + moved
    errs = L.validate_collection(new)
    if errs:
        raise SystemExit("Refusing to publish, schema errors:\n" + "\n".join(errs))
    new.sort(key=lambda e: (e["month"], e.get("start_date") or "9999", e["name"].lower()))
    return new, rest, [m["id"] for m in moved]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", action="append", default=[])
    ap.add_argument("--reject", action="append", default=[])
    ap.add_argument("--reason")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args(argv)
    queue = L.load(L.QUEUE)
    if a.approve or a.reject:
        set_status(queue, a.approve, "approved")
        set_status(queue, a.reject, "rejected", a.reason)
        L.save(L.QUEUE, queue)
        print(f"approved {a.approve} rejected {a.reject}")
        return 0
    events, rest, ids = publish(L.load(L.EVENTS), queue)
    L.save(L.EVENTS, events)
    L.save(L.QUEUE, rest)
    print(f"published {len(ids)}: {ids}")
    if not a.no_build:
        build.build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
