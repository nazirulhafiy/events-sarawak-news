"""Discover candidate Sarawak event URLs from data/sources.json (mirrors ai.sarawak.news ingest.py).

Output is internal review material only (dist/candidate-urls.json). A human or
the Cloud Agent opens each URL, verifies the facts and writes a candidate
manifest (automation/candidate.schema.json) for scripts/queue.py.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "candidate-urls.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import events_lib as L  # noqa: E402

EVENT_WORDS = ["festival", "pesta", "regatta", "regata", "marathon", "run", "trail", "carnival", "karnival",
               "gawai", "concert", "championship", "kejohanan", "fiesta", "expo", "fair", "parade", "race",
               "challenge", "kaul", "jamboree", "summit", "open house", "tournament", "safari", "event"]
PLACE_WORDS = ["sarawak", "kuching", "miri", "sibu", "bintulu", "mukah", "kapit", "limbang", "lawas", "betong",
               "sri aman", "serian", "samarahan", "sarikei", "bau", "lundu", "belaga", "bario", "santubong"]
DATE_RE = re.compile(r"\b(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", re.I)


def load_sources() -> list[dict]:
    return json.loads((ROOT / "data" / "sources.json").read_text())


def fetch(url: str, timeout: int = 12) -> tuple[int, str]:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (events.sarawak.news discovery)"})
    with urlopen(req, timeout=timeout) as r:
        return r.status, r.read(2_000_000).decode("utf-8", "replace")


def links_from_page(base: str, body: str):
    for href, text in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', body, re.S | re.I):
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 12:
            yield urljoin(base, href), text


def score(title: str, url: str) -> tuple[int, list[str]]:
    hay = f"{title} {url}".lower()
    ev = [w for w in EVENT_WORDS if re.search(rf"\b{re.escape(w)}\b", hay)]
    pl = [w for w in PLACE_WORDS if w in hay]
    s = 2 * len(ev) + len(pl) + (2 if DATE_RE.search(title) else 0)
    return (s if ev else 0), ev + pl


def known_names() -> set[str]:
    pool = L.load(L.EVENTS) + L.load(L.QUEUE)
    return {L._norm_name(e["name"]) for e in pool} | {e.get("source_url") for e in pool}


def discover(limit_per_source: int, min_score: int) -> list[dict]:
    known = known_names()
    seen, out = set(), []
    for src in load_sources():
        try:
            _, body = fetch(src["url"])
        except Exception as exc:  # noqa: BLE001 - report, keep going
            print(f"WARN {src['name']}: {exc}", file=sys.stderr)
            continue
        host = urlparse(src["url"]).netloc
        found = []
        for url, title in links_from_page(src["url"], body):
            if url in seen or urlparse(url).netloc.split(":")[0].removeprefix("www.") != host.removeprefix("www."):
                continue
            sc, matched = score(title, url)
            if sc < min_score:
                continue
            seen.add(url)
            found.append({"title": title, "url": url, "score": sc, "matched": matched,
                          "source": src["name"], "discovery_source_url": src["url"],
                          "maybe_known": url in known or L._norm_name(title) in known})
        found.sort(key=lambda c: -c["score"])
        out += found[:limit_per_source]
        time.sleep(0.5)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit-per-source", type=int, default=8)
    ap.add_argument("--min-score", type=int, default=3)
    ap.add_argument("--output", type=Path, default=OUT)
    a = ap.parse_args(argv)
    cands = discover(a.limit_per_source, a.min_score)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(cands, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(cands)} candidate URLs -> {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
