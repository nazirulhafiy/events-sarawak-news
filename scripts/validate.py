"""Validate data/events.json and data/review-queue.json against the event schema."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import events_lib as L  # noqa: E402

errs = L.validate_collection(L.load(L.EVENTS)) + L.validate_collection(L.load(L.QUEUE))
bad = [e for e in L.load(L.EVENTS) if e["status"] not in ("published", "cancelled")]
errs += [f"{e['id']}: events.json may only hold published/cancelled" for e in bad]
print("\n".join(errs) if errs else "OK: events and review queue match the schema")
sys.exit(1 if errs else 0)
