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
        self.assertEqual(len(self.events), 106)
        for ev in self.events:
            for k in ("id", "name", "month", "division", "summary", "date_tbc"):
                self.assertIn(k, ev)
            self.assertTrue(1 <= ev["month"] <= 12)

    def test_unique_ids(self):
        ids = [ev["id"] for ev in self.events]
        self.assertEqual(len(ids), len(set(ids)))

    def test_dates_valid_and_ordered(self):
        for ev in self.events:
            if ev["start_date"] and not ev["date_tbc"]:
                s = dt.date.fromisoformat(ev["start_date"])
                self.assertEqual(s.year, 2026)
                self.assertEqual(s.month, ev["month"], ev["id"])
                if ev["end_date"]:
                    self.assertGreaterEqual(dt.date.fromisoformat(ev["end_date"]), s)

    def test_month_counts_match_review(self):
        c = build.month_counts(self.events)
        self.assertEqual([c[m] for m in range(1, 13)], [2, 1, 2, 14, 13, 13, 14, 12, 21, 10, 3, 1])


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
        self.assertIn('>Oct <span class="category-filter-count" aria-hidden="true">10</span>', tabs[9])
        self.assertEqual(sum('aria-selected="true"' in t for t in tabs), 1)

    def test_only_current_panel_visible(self):
        panels = re.findall(r'<ol class="event-list"[^>]*>', self.html)
        self.assertEqual(len(panels), 12)
        visible = [p for p in panels if " hidden" not in p]
        self.assertEqual(len(visible), 1)
        self.assertIn('data-panel="10"', visible[0])

    def test_all_events_rendered(self):
        self.assertEqual(self.html.count('class="event-card"'), 106)
        self.assertEqual(self.html.count('class="event-type"'), 106)

    def test_no_event_note_or_division_filter(self):
        self.assertNotIn('class="event-note"', self.html)
        self.assertNotIn("data-division", self.html)
        self.assertNotIn("Browse by division", self.html)

    def test_footer_categories_and_card_type_data(self):
        self.assertIn('class="site-footer-categories-title">Categories</h2>', self.html)
        self.assertIn(
            '<a class="site-footer-link" href="mailto:contact@sarawak.news">Contact</a>',
            self.html,
        )
        for kind, label in (
            ("festival", "Festival"),
            ("sports", "Sports"),
            ("cultural", "Cultural"),
            ("concert", "Concert"),
        ):
            self.assertIn(f'href="/?event_type={kind}">{label}</a>', self.html)
        self.assertEqual(self.html.count('data-event-type="'), 106)
        about = build.render_about(self.events, self.now)
        self.assertIn('href="/?event_type=festival">Festival</a>', about)
        self.assertIn(
            '<a class="site-footer-link" href="mailto:contact@sarawak.news">Contact</a>',
            about,
        )

    def test_cloudflare_and_ga4_in_head(self):
        site = json.loads(build.SITE_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(list(site), ["ga4_measurement_id"])
        self.assertEqual(site["ga4_measurement_id"], "G-P7Y5Z19Q46")
        head, _, body = self.html.partition("</head>")
        self.assertIn("static.cloudflareinsights.com/beacon.min.js", head)
        self.assertIn("092a061973fc4d899cd2e4b52952af89", head)
        self.assertIn('content="index,follow"', head)
        self.assertNotIn("noindex", head)
        self.assertIn('<link rel="canonical" href="https://events.sarawak.news/" />', head)
        self.assertIn("https://www.googletagmanager.com/gtag/js?id=G-P7Y5Z19Q46", head)
        self.assertIn("gtag('config','G-P7Y5Z19Q46')", head)
        self.assertNotIn("googletagmanager", body)
        about = build.render_about(self.events, self.now)
        about_head, _, _ = about.partition("</head>")
        self.assertIn("gtag('config','G-P7Y5Z19Q46')", about_head)
        self.assertIn("static.cloudflareinsights.com/beacon.min.js", about)

    def test_blank_ga_measurement_id_omits_gtag(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "site.json").write_text(
                json.dumps({"ga4_measurement_id": ""}), encoding="utf-8")
            original = build.SITE_CONFIG
            build.SITE_CONFIG = root / "site.json"
            try:
                out = build.build(root / "dist", self.now)
                pages = [
                    (out / name).read_text(encoding="utf-8")
                    for name in ("index.html", "about.html", "404.html")
                ]
            finally:
                build.SITE_CONFIG = original
        for page in pages:
            self.assertNotIn("gtag", page)
            self.assertNotIn("googletagmanager", page)
            self.assertNotIn("G-P7Y5Z19Q46", page)
            self.assertIn("static.cloudflareinsights.com/beacon.min.js", page)
            self.assertIn('content="index,follow"', page)
            self.assertNotIn("noindex", page)

    def test_date_labels(self):
        self.assertEqual(
            build.meta_date({"start_date": "2026-10-15", "end_date": None, "month": 10, "date_tbc": False}),
            ("15 OCT 2026", "2026-10-15"),
        )
        self.assertEqual(
            build.meta_date({"start_date": "2026-10-02", "end_date": "2026-10-04", "month": 10, "date_tbc": False})[0],
            "2\u20134 OCT 2026",
        )
        self.assertEqual(
            build.meta_date({"start_date": "2026-07-22", "end_date": "2026-08-16", "month": 7, "date_tbc": False})[0],
            "22 JUL\u201316 AUG 2026",
        )
        self.assertEqual(
            build.meta_date({"start_date": "2026-12-30", "end_date": "2027-01-02", "month": 12, "date_tbc": False})[0],
            "30 DEC 2026\u20132 JAN 2027",
        )
        self.assertEqual(
            build.meta_date({"start_date": None, "end_date": None, "month": 5, "date_tbc": True}),
            ("TBC", None),
        )

    def test_meta_row_is_date_and_place_only(self):
        card = build.render_card({
            "id": "x", "name": "Regatta", "month": 10,
            "start_date": "2026-10-02", "end_date": "2026-10-04", "date_tbc": False,
            "summary": "A river race.", "venue": "Waterfront", "town": "Bau", "division": "Kuching",
        })
        self.assertIn('class="event-meta-row"', card)
        self.assertIn(">2\u20134 OCT 2026<", card)
        self.assertIn('datetime="2026-10-02"', card)
        self.assertIn('class="event-place-label">Bau<', card)
        self.assertNotIn("event-place-label\">Kuching", card)
        self.assertNotIn("event-date", card)
        self.assertNotIn("event-chip", card)
        self.assertNotIn("event-type", card)
        self.assertNotIn("story-section", card)
        self.assertNotIn("story-source", card)
        typed = build.render_card({
            "id": "r", "name": "Regatta", "month": 10,
            "start_date": "2026-10-30", "end_date": "2026-11-01", "date_tbc": False,
            "summary": "A river regatta.", "venue": "Waterfront", "town": "Kuching",
            "division": "Kuching", "event_type": "sports",
        })
        self.assertIn('class="event-type">sports<', typed)
        self.assertIn('class="event-place-label">Kuching<', typed)
        fallback = build.render_card({
            "id": "y", "name": "Undated", "month": 5,
            "start_date": None, "end_date": None, "date_tbc": True,
            "summary": "Date not fixed.", "venue": "", "town": "", "division": "Miri",
        })
        self.assertIn('class="event-when">TBC<', fallback)
        self.assertIn('class="event-place-label">Miri<', fallback)
        self.assertNotIn("<time", fallback)
        linked = build.render_card({
            "id": "z", "name": "Mart", "month": 8,
            "start_date": "2026-08-18", "end_date": "2026-08-20", "date_tbc": False,
            "summary": "A travel mart.", "venue": "BCCK", "town": "Kuching", "division": "Kuching",
            "official_url": "https://www.pata.org/pata-travel-mart-2026",
        })
        self.assertIn('class="event-link" href="https://www.pata.org/pata-travel-mart-2026"', linked)
        self.assertIn('tabindex="0"', linked)
        self.assertIn('aria-label="Open event: Mart"', linked)
        self.assertNotIn("Official site", linked)
        self.assertNotIn("event-links", linked)
        self.assertIn("Venue", linked)
        self.assertIn("A travel mart.", linked)
        plain = build.render_card({
            "id": "plain", "name": "Walk", "month": 1,
            "start_date": "2026-01-01", "end_date": "2026-01-01", "date_tbc": False,
            "summary": "A walk.", "venue": "Park", "town": "Kuching", "division": "Kuching",
        })
        self.assertNotIn("event-link", plain)
        self.assertNotIn("tabindex=", plain)

    def test_card_type_and_hover_only_when_linked(self):
        css = (build.SITE / "events.css").read_text()
        self.assertIn(
            ".event-name { margin: 0; font-size: 17px; font-weight: 800; line-height: 1.35; letter-spacing: -.012em; }",
            css,
        )
        self.assertIn(
            ".event-sum { margin: 8px 0; color: var(--muted); font-size: 13px; line-height: 1.55; }",
            css,
        )
        self.assertNotIn(".event-name { font-size: 18px; }", css)
        self.assertIn(".event-card:has(.event-link):hover", css)
        self.assertIn(".js .event-card:not(.is-revealed)", css)
        self.assertIn("animation: story-reveal .7s cubic-bezier(.22, 1, .36, 1) both", css)
        self.assertNotIn(".event-card:hover {", css)
        self.assertNotIn("event-links", css)

    def test_info_link_and_hover_when_either_url_is_set(self):
        css = (build.SITE / "events.css").read_text()
        js = (build.SITE / "events.js").read_text()
        self.assertIn(".event-card:has(.event-link):hover", css)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("is-revealed", js)
        self.assertNotIn(".event-card:hover {", css)
        self.assertNotIn("Official site", self.html)
        self.assertNotIn("More information", self.html)
        self.assertEqual(self.html.count('class="event-link"'), 17)
        self.assertIn(
            'href="https://suarasarawak.my/festival-kucing-antarabangsa-bakal-berlangsung-oktober-ini/"',
            self.html,
        )
        self.assertIn(
            'href="https://suarasarawak.my/muaythai-piala-premier-sarawak-2026-pertembungan-300-peserta-di-bintulu/"',
            self.html,
        )
        self.assertIn(
            'href="https://suarasarawak.my/karnival-siburan-platform-ketengah-produk-budaya-tempatan/"',
            self.html,
        )
        self.assertIn('href="https://www.santubongtrail.com/"', self.html)
        self.assertNotIn("intourcams.my", self.html)
        self.assertIn(
            'href="https://limbang.sarawak.gov.my/web/subpage/news_view/941"',
            self.html,
        )
        self.assertNotIn("Suara Sarawak", self.html)
        self.assertNotIn("Borneo Post", self.html)
        cat = self.html.split('id="kuching-international-cat-festival-2026"', 1)[1].split("</li>", 1)[0]
        self.assertIn('class="event-link"', cat)
        self.assertNotIn("More information", cat)
        self.assertNotIn("Official site", cat)

    def test_undated_sorted_last(self):
        may = sorted([e for e in self.events if e["month"] == 5], key=build.sort_key)
        self.assertEqual(may[-1]["id"], "bukit-sadok-expedition-2026")

    def test_escaping(self):
        card = build.render_card({"id": "x", "name": "A <b>&", "month": 1, "start_date": None, "end_date": None,
                                  "summary": "", "venue": "", "town": "<i>", "division": "", "organiser": ""})
        self.assertIn("A &lt;b&gt;&amp;", card)
        self.assertIn("&lt;i&gt;", card)
        self.assertNotIn("event-place-label\"><i>", card)

    def test_no_custom_domain_or_hub_link(self):
        self.assertNotIn('href="https://sarawak.news', self.html)

    def test_hidden_panels_not_overridden_by_css(self):
        css = (build.SITE / "events.css").read_text()
        self.assertIn(".event-list[hidden] { display: none; }", css)

    def test_build_writes_dist(self):
        with tempfile.TemporaryDirectory() as d:
            out = build.build(Path(d) / "dist", self.now)
            for f in (
                "index.html",
                "about.html",
                "style.css",
                "events.css",
                "app.js",
                "events.js",
                "fonts/Geist-Variable.woff2",
                "icons/nav-mark-transparent.svg",
                "icons/nav-mark-transparent-dark.svg",
            ):
                self.assertTrue((out / f).exists(), f)
            icons = build.SITE / "icons"
            self.assertEqual(
                (out / "icons" / "nav-mark-transparent.svg").read_bytes(),
                (icons / "nav-mark-transparent.svg").read_bytes(),
            )
            self.assertEqual(
                (out / "icons" / "nav-mark-transparent-dark.svg").read_bytes(),
                (icons / "nav-mark-transparent-dark.svg").read_bytes(),
            )
            self.assertEqual((out / "CNAME").read_text(encoding="utf-8"), "events.sarawak.news\n")
            robots = (out / "robots.txt").read_text(encoding="utf-8")
            self.assertEqual(
                robots,
                "User-agent: *\nAllow: /\nSitemap: https://events.sarawak.news/sitemap.xml\n",
            )
            self.assertNotIn("noindex", robots)
            sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("<loc>https://events.sarawak.news/</loc>", sitemap)
            self.assertIn("<loc>https://events.sarawak.news/about.html</loc>", sitemap)
            self.assertIn("<lastmod>2026-10-15</lastmod>", sitemap)
            self.assertNotIn("404.html", sitemap)
            canonicals = {
                "index.html": "https://events.sarawak.news/",
                "about.html": "https://events.sarawak.news/about.html",
                "404.html": "https://events.sarawak.news/404.html",
            }
            for name, canonical in canonicals.items():
                page = (out / name).read_text(encoding="utf-8")
                head, _, _ = page.partition("</head>")
                self.assertIn("gtag('config','G-P7Y5Z19Q46')", head)
                self.assertIn("static.cloudflareinsights.com/beacon.min.js", page)
                self.assertIn('content="index,follow"', head)
                self.assertNotIn("noindex", page)
                self.assertIn(f'<link rel="canonical" href="{canonical}" />', head)
                self.assertNotIn('href="https://sarawak.news', page)
                self.assertIn('src="icons/nav-mark-transparent.svg"', page)
                self.assertIn('src="icons/nav-mark-transparent-dark.svg"', page)
                self.assertIn('class="brand-text">Events.Sarawak.News</span>', page)
                self.assertNotIn("nav-mark-on-black", page)


if __name__ == "__main__":
    unittest.main()
