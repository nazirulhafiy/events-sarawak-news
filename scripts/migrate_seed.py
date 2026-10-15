"""One-off: migrate the 2026 seed (data/events-2026.json, old shape) to data/events.json.

Kept for the record; re-running is idempotent. Drops phone, email, organiser
and website fields, and strips contact details from notes.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import events_lib as L  # noqa: E402

SEED_URL = "https://mtcp.sarawak.gov.my/"
SEED_NAME = "Seed: Sarawak 2026 Calendar of Tourism Events (MTCP)"
SEED_AT = "2026-10-15T00:00:00+08:00"


def clean_note(note: str) -> str | None:
    note = note.replace("Dates subject to change.", "").strip()
    parts = [p.strip() for p in re.split(r"(?<=[.;])\s+", note) if p.strip()]
    keep = [p for p in parts if not (L.PHONE_RE.search(p) or L.EMAIL_RE.search(p) or "phone" in p.lower())]
    out = " ".join(keep).strip()
    return out or None


def migrate(old: list[dict]) -> list[dict]:
    out = []
    for e in old:
        ev = {
            "id": e["id"], "name": e["name"], "start_date": e["start_date"], "end_date": e["end_date"],
            "date_tbc": not e["start_date"], "month": e["month"], "venue": e["venue"] or None,
            "town": e["town"], "division": e["division"], "summary": e["summary"],
            "official_url": e.get("website") or None, "source_url": SEED_URL, "source_name": SEED_NAME,
            "discovered_at": SEED_AT, "status": "published",
        }
        note = clean_note(e.get("notes") or "")
        if note:
            ev["review_note"] = note
        out.append(ev)
    return out


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else L.ROOT / "data" / "events-2026.json"
    events = migrate(json.loads(src.read_text()))
    errs = L.validate_collection(events)
    if errs:
        print("\n".join(errs)); sys.exit(1)
    L.save(L.EVENTS, events)
    print(f"Wrote {len(events)} events to {L.EVENTS}")
