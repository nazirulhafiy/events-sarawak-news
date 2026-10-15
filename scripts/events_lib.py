"""Standard event schema for events.sarawak.news: validation, normalisation, dedupe.

See docs/schema.md. Standard library only.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "data" / "events.json"
QUEUE = ROOT / "data" / "review-queue.json"
MYT = dt.timezone(dt.timedelta(hours=8))

DIVISIONS = {"Betong", "Bintulu", "Kapit", "Kuching", "Limbang", "Miri", "Mukah",
             "Samarahan", "Sarikei", "Serian", "Sibu", "Sri Aman"}
STATUSES = {"published", "pending", "approved", "rejected", "duplicate", "cancelled"}
PUBLIC_FIELDS = ["id", "name", "start_date", "end_date", "date_tbc", "month", "venue",
                 "town", "division", "summary", "official_url"]
INTERNAL_FIELDS = ["source_url", "source_name", "discovered_at", "status", "review_note"]
ALL_FIELDS = PUBLIC_FIELDS + INTERNAL_FIELDS
REQUIRED = ["id", "name", "date_tbc", "month", "town", "division", "summary",
            "source_url", "source_name", "discovered_at", "status"]
SUMMARY_MAX = 280
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Malaysian phone shapes: 0xx-xxx xxxx, 08x-xxx xxx, +60...
PHONE_RE = re.compile(r"(?:\+?60[\s-]?|\b0)\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,4}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("'", "")).strip("-")


def make_id(name: str, year: int) -> str:
    base = slugify(name)
    return base if base.endswith(str(year)) else f"{base}-{year}"


def _date(v):
    return dt.date.fromisoformat(v) if v else None


def validate_event(ev: dict) -> list[str]:
    """Return a list of problems (empty when valid)."""
    errs = []
    eid = ev.get("id", "?")
    for k in ev:
        if k not in ALL_FIELDS:
            errs.append(f"{eid}: unknown field '{k}'")
    for k in REQUIRED:
        if k not in ev or ev[k] in (None, ""):
            errs.append(f"{eid}: missing '{k}'")
    if errs:
        return errs
    if not ID_RE.match(ev["id"]):
        errs.append(f"{eid}: id must be a lowercase slug")
    if ev["status"] not in STATUSES:
        errs.append(f"{eid}: bad status '{ev['status']}'")
    if ev["division"] not in DIVISIONS:
        errs.append(f"{eid}: unknown division '{ev['division']}'")
    if not isinstance(ev["date_tbc"], bool):
        errs.append(f"{eid}: date_tbc must be boolean")
    try:
        s, f = _date(ev.get("start_date")), _date(ev.get("end_date"))
    except ValueError as exc:
        return errs + [f"{eid}: bad date ({exc})"]
    if not (isinstance(ev["month"], int) and 1 <= ev["month"] <= 12):
        errs.append(f"{eid}: month must be 1-12")
    if ev["date_tbc"]:
        if f and not s:
            errs.append(f"{eid}: end_date without start_date")
    else:
        if not s:
            errs.append(f"{eid}: start_date required unless date_tbc")
        elif s.month != ev["month"]:
            errs.append(f"{eid}: month does not match start_date")
    if s and f and f < s:
        errs.append(f"{eid}: end_date before start_date")
    summ = ev["summary"]
    if len(summ) > SUMMARY_MAX:
        errs.append(f"{eid}: summary longer than {SUMMARY_MAX} chars")
    if len(re.findall(r"[.!?](?:\s|$)", summ)) > 2:
        errs.append(f"{eid}: summary must be 1-2 sentences")
    for k in ("official_url", "source_url"):
        v = ev.get(k)
        if v and not str(v).startswith("https://"):
            errs.append(f"{eid}: {k} must be https")
    for k in PUBLIC_FIELDS + ["review_note"]:
        v = ev.get(k)
        if isinstance(v, str) and (PHONE_RE.search(v) or EMAIL_RE.search(v)):
            errs.append(f"{eid}: '{k}' contains a phone number or email")
    return errs


def validate_collection(events: list[dict]) -> list[str]:
    errs = []
    seen = set()
    for ev in events:
        errs += validate_event(ev)
        if ev.get("id") in seen:
            errs.append(f"{ev.get('id')}: duplicate id")
        seen.add(ev.get("id"))
    return errs


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def save(path: Path, events: list[dict]) -> None:
    ordered = [{k: ev.get(k) for k in ALL_FIELDS if k in ev} for ev in events]
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def public(events: list[dict]) -> list[dict]:
    """Published events with internal fields stripped."""
    return [{k: ev.get(k) for k in PUBLIC_FIELDS} for ev in events if ev.get("status") == "published"]


def _norm_name(name: str) -> str:
    n = slugify(name)
    n = re.sub(r"-(20\d\d|\d+(st|nd|rd|th)|edisi-ke-\d+)\b", "", n)
    return n


def find_duplicate(ev: dict, pool: list[dict]) -> dict | None:
    """Same id, same official/source URL, or same normalised name with overlapping dates."""
    name = _norm_name(ev["name"])
    s, f = _date(ev.get("start_date")), _date(ev.get("end_date"))
    for other in pool:
        if other is ev:
            continue
        if other.get("id") == ev.get("id"):
            return other
        if ev.get("official_url") and ev.get("official_url") == other.get("official_url"):
            return other
        if _norm_name(other["name"]) == name:
            os_, of = _date(other.get("start_date")), _date(other.get("end_date"))
            if not s or not os_:
                if ev.get("month") == other.get("month"):
                    return other
                continue
            if s <= (of or os_) and os_ <= (f or s):
                return other
    return None


def normalise_candidate(c: dict, now: dt.datetime | None = None) -> dict:
    """Turn a candidate-manifest entry into a schema event with status 'pending'."""
    now = (now or dt.datetime.now(MYT)).astimezone(MYT)
    s = c.get("start_date") or None
    f = c.get("end_date") or None
    if f == s:
        f = None
    year = int((s or c.get("year") or now.year).__str__()[:4])
    month = int(s[5:7]) if s else int(c["month"])
    town = (c.get("town") or "").strip()
    ev = {
        "id": make_id(c["name"], year),
        "name": re.sub(r"\s+", " ", c["name"]).strip(),
        "start_date": s,
        "end_date": f,
        "date_tbc": not bool(s),
        "month": month,
        "venue": (c.get("venue") or "").strip() or None,
        "town": town,
        "division": c.get("division") or "",
        "summary": re.sub(r"\s+", " ", c.get("summary") or "").strip(),
        "official_url": c.get("official_url") or None,
        "source_url": c["url"],
        "source_name": c["source"],
        "discovered_at": c.get("discovered_at") or now.isoformat(timespec="seconds"),
        "status": "pending",
    }
    return ev
