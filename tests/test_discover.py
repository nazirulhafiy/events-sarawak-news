"""Unit tests for scripts/discover.py social-source handling."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import discover as D  # noqa: E402


class SocialSourceTests(unittest.TestCase):
    def test_is_social_by_category(self):
        self.assertTrue(D.is_social_source({
            "name": "Example — Facebook",
            "url": "https://example.com/page",
            "category": "social",
        }))

    def test_is_social_by_host(self):
        self.assertTrue(D.is_social_source({
            "name": "FB",
            "url": "https://www.facebook.com/visitsarawak",
            "category": "official tourism",
        }))
        self.assertTrue(D.is_social_source({
            "name": "IG",
            "url": "https://www.instagram.com/sarawaktravel/",
        }))
        self.assertFalse(D.is_social_source({
            "name": "Web",
            "url": "https://sarawaktourism.com/events",
            "category": "official tourism",
        }))

    def test_social_browser_lead_shape(self):
        src = {
            "name": "STB — Facebook",
            "url": "https://www.facebook.com/visitsarawak",
            "category": "social",
            "notes": "Tourism festivals.",
        }
        lead = D.social_browser_lead(src)
        self.assertEqual(lead["url"], src["url"])
        self.assertTrue(lead["needs_browser"])
        self.assertIn("needs_browser", lead["matched"])
        self.assertEqual(lead["note"], "Tourism festivals.")
        self.assertEqual(lead["score"], 0)

    def test_discover_emits_social_leads_without_fetch(self):
        sources = [
            {"name": "STB — Facebook", "url": "https://www.facebook.com/visitsarawak",
             "category": "social", "notes": "Festivals."},
            {"name": "Example site", "url": "https://example.invalid/events",
             "category": "news"},
        ]
        html = (
            '<a href="/fest-kuching-2026">Kuching Festival 2026 Santubong</a>'
            '<a href="/about">About</a>'
        )
        with mock.patch.object(D, "load_sources", return_value=sources), \
             mock.patch.object(D, "fetch", return_value=(200, html)) as fetch_mock, \
             mock.patch.object(D, "known_names", return_value=set()), \
             mock.patch.object(D.time, "sleep"):
            out = D.discover(limit_per_source=8, min_score=3)
        fetch_mock.assert_called_once_with("https://example.invalid/events")
        social = [c for c in out if c.get("needs_browser")]
        self.assertEqual(len(social), 1)
        self.assertEqual(social[0]["url"], "https://www.facebook.com/visitsarawak")
        self.assertTrue(any(c["url"].endswith("/fest-kuching-2026") for c in out))

    def test_sources_json_social_entries(self):
        sources = json.loads((ROOT / "data" / "sources.json").read_text())
        social = [s for s in sources if s.get("category") == "social"]
        self.assertGreaterEqual(len(social), 10)
        for s in social:
            self.assertTrue(s["url"].startswith("https://"), s)
            host = D.host_of(s["url"])
            self.assertTrue(
                any(host == h or host.endswith("." + h) for h in D.SOCIAL_HOST_SUFFIXES),
                s,
            )
            self.assertTrue(s.get("notes"), s)
            self.assertEqual(s.get("expected_yield"), "browser")


if __name__ == "__main__":
    unittest.main()
