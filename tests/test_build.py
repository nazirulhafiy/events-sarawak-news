import datetime as dt
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402

MYT = build.MYT


class DataTests(unittest.TestCase):
    def setUp(self):
        self.events = build.load_events()

    def test_count_and_fields(self):
        self.assertEqual(len(self.events), 114)
        for ev in self.events:
            for k in ("id", "name", "month", "division", "summary"):
                self.assertIn(k, ev)
            self.assertTrue(1 <= ev["month"] <= 12)

    def test_unique_ids(self):
        ids = [ev["id"] for ev in self.events]
        self.assertEqual(len(ids), len(set(ids)))

    def test_dates_valid_and_ordered(self):
        for ev in self.events:
            if ev["start_date"]:
                s = dt.date.fromisoformat(ev["start_date"])
                self.assertEqual(s.year, 2026)
                self.assertEqual(s.month, ev["month"], ev["id"])
                if ev["end_date"]:
                    self.assertGreaterEqual(dt.date.fromisoformat(ev["end_date"]), s)

    def test_month_counts_match_review(self):
        c = build.month_counts(self.events)
        self.assertEqual([c[m] for m in range(1, 13)], [2, 1, 2, 14, 13, 13, 14, 11, 21, 15, 4, 4])


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.events = build.load_events()
        self.now = dt.datetime(2026, 10, 15, 22, 0, tzinfo=MYT)
        self.html = build.render_index(self.events, self.now)

    def test_default_month_uses_myt(self):
        # 16:30 UTC on 31 Oct is already 1 Nov in Kuching.
        utc = dt.datetime(2026, 10, 31, 16, 30, tzinfo=dt.timezone.utc)
        self.assertEqual(build.default_month(utc), 11)
        self.assertEqual(build.default_month(dt.datetime(2025, 6, 1, tzinfo=MYT)), 1)
        self.assertEqual(build.default_month(dt.datetime(2027, 6, 1, tzinfo=MYT)), 12)

    def test_tabs_have_counts_and_current_selected(self):
        tabs = re.findall(r'<button type="button" role="tab".*?</button>', self.html)
        self.assertEqual(len(tabs), 12)
        self.assertIn('aria-selected="true"', tabs[9])
        self.assertIn('>Oct <span class="category-filter-count" aria-hidden="true">15</span>', tabs[9])
        self.assertEqual(sum('aria-selected="true"' in t for t in tabs), 1)

    def test_only_current_panel_visible(self):
        panels = re.findall(r'<ol class="event-list"[^>]*>', self.html)
        self.assertEqual(len(panels), 12)
        visible = [p for p in panels if " hidden" not in p]
        self.assertEqual(len(visible), 1)
        self.assertIn('data-panel="10"', visible[0])

    def test_all_events_rendered(self):
        self.assertEqual(self.html.count('class="event-card"'), 114)

    def test_note_present_and_no_division_filter(self):
        self.assertIn("Dates subject to change, check with organisers", self.html)
        self.assertNotIn("data-division", self.html)
        self.assertNotIn("Browse by division", self.html)

    def test_cloudflare_analytics_no_ga(self):
        self.assertIn("static.cloudflareinsights.com/beacon.min.js", self.html)
        self.assertIn("092a061973fc4d899cd2e4b52952af89", self.html)
        self.assertNotIn("googletagmanager", self.html)

    def test_date_labels(self):
        ev = {"start_date": "2026-07-22", "end_date": "2026-08-16", "month": 7}
        self.assertEqual(build.date_parts(ev)[:2], ("22\u201316", "Jul\u2013Aug"))
        self.assertEqual(build.date_parts({"start_date": "2026-10-03", "end_date": None, "month": 10})[:2], ("3", "Oct"))
        self.assertEqual(build.date_parts({"start_date": None, "end_date": None, "month": 5})[0], "TBC")

    def test_undated_sorted_last(self):
        may = sorted([e for e in self.events if e["month"] == 5], key=build.sort_key)
        self.assertEqual(may[-1]["id"], "bukit-sadok-expedition-2026")

    def test_escaping(self):
        card = build.render_card({"id": "x", "name": "A <b>&", "month": 1, "start_date": None, "end_date": None,
                                  "summary": "", "venue": "", "town": "", "division": "", "organiser": ""})
        self.assertIn("A &lt;b&gt;&amp;", card)

    def test_no_custom_domain_or_hub_link(self):
        self.assertNotIn('href="https://sarawak.news', self.html)

    def test_hidden_panels_not_overridden_by_css(self):
        css = (build.SITE / "events.css").read_text()
        self.assertIn(".event-list[hidden] { display: none; }", css)

    def test_build_writes_dist(self):
        with tempfile.TemporaryDirectory() as d:
            out = build.build(Path(d) / "dist", self.now)
            for f in ("index.html", "about.html", "style.css", "events.css", "app.js", "events.js", "fonts/Geist-Variable.woff2"):
                self.assertTrue((out / f).exists(), f)
            self.assertFalse((out / "CNAME").exists())


if __name__ == "__main__":
    unittest.main()
