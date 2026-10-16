import copy
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402
import events_lib as L  # noqa: E402
import publish  # noqa: E402
import queue as q  # noqa: E402

GOOD = {"id": "test-fest-2026", "name": "Test Fest", "start_date": "2026-11-05", "end_date": "2026-11-07",
        "date_tbc": False, "month": 11, "venue": "Kuching Waterfront", "town": "Kuching", "division": "Kuching",
        "summary": "A test festival on the waterfront.", "event_type": "festival", "official_url": None,
        "source_url": "https://example.com/a", "source_name": "Example", "discovered_at": "2026-10-15T10:00:00+08:00",
        "status": "published"}


def cand(**kw):
    c = {"name": "Kuching Lantern Walk", "start_date": "2026-12-12", "end_date": None, "month": 12, "venue": "Padang Merdeka",
         "town": "Kuching", "division": "Kuching", "summary": "A lantern walk through the old town.",
         "url": "https://dayakdaily.com/lantern", "source": "DayakDaily", "language_verified": True,
         "discovered_at": "2026-10-15T10:00:00+08:00", "source_checked_at": "2026-10-15T10:05:00+08:00",
         "discovery_source_url": "https://dayakdaily.com/?s=festival"}
    c.update(kw)
    return c


def manifest(*cs):
    return {"schema_version": 1, "run_id": "t1", "generated_at": "2026-10-15T10:00:00+08:00",
            "timezone": "Asia/Kuching", "candidates": list(cs)}


class SeedData(unittest.TestCase):
    def setUp(self):
        self.events = L.load(L.EVENTS)

    def test_all_114_seed_events_valid(self):
        self.assertEqual(len(self.events), 114)
        self.assertEqual(L.validate_collection(self.events), [])
        statuses = {e["status"] for e in self.events}
        self.assertEqual(statuses, {"published", "cancelled"})
        self.assertEqual(sum(1 for e in self.events if e["status"] == "published"), 112)
        self.assertEqual(sum(1 for e in self.events if e["status"] == "cancelled"), 2)

    def test_only_schema_fields(self):
        for e in self.events:
            self.assertLessEqual(set(e), set(L.ALL_FIELDS), e["id"])
            for gone in ("phone", "email", "organiser", "website", "notes", "source"):
                self.assertNotIn(gone, e)

    def test_no_phone_or_email_anywhere_in_data(self):
        for p in (L.EVENTS, L.QUEUE):
            text = p.read_text()
            self.assertIsNone(L.PHONE_RE.search(text), p)
            self.assertIsNone(L.EMAIL_RE.search(text), p)

    def test_date_tbc_events(self):
        tbc = {e["id"] for e in self.events if e["date_tbc"]}
        self.assertEqual(tbc, {"bukit-sadok-expedition-2026"})

    def test_queue_valid(self):
        self.assertEqual(L.validate_collection(L.load(L.QUEUE)), [])

    def test_published_events_are_typed(self):
        counts = {}
        for ev in self.events:
            self.assertIn(ev.get("event_type"), L.EVENT_TYPES, ev["id"])
            counts[ev["event_type"]] = counts.get(ev["event_type"], 0) + 1
        self.assertEqual(sum(counts.values()), len(self.events))
        self.assertEqual(set(counts), set(L.EVENT_TYPES))

    def test_published_info_urls(self):
        linked = {e["id"]: e["info_url"] for e in self.events if e.get("info_url")}
        self.assertEqual(linked, {
            "kuching-international-cat-festival-2026":
                "https://suarasarawak.my/festival-kucing-antarabangsa-bakal-berlangsung-oktober-ini/",
            "kejohanan-muaythai-piala-premier-sarawak-edisi-ke-10-2026":
                "https://suarasarawak.my/muaythai-piala-premier-sarawak-2026-pertembungan-300-peserta-di-bintulu/",
            "karnival-siburan-2026":
                "https://suarasarawak.my/karnival-siburan-platform-ketengah-produk-budaya-tempatan/",
            "karnival-balau-dalat-2026":
                "https://utusansarawak.com.my/industri-balau-terus-diperkasa-jadi-bank-ekonomi-masyarakat-dalat/",
            "pesta-tabih-long-bemang-2026":
                "https://www.intourcams.my/events",
            "pesta-kebudayaan-apau-koyan-2026":
                "https://www.intourcams.my/events",
            "krian-fest-nature-challenge-edisi-ke-4-2026":
                "https://utusansarawak.com.my/pesta-saratok-2026-dan-krian-fest-nature-challenge-kembali-meriahkan-kriansaratok/",
            "serian-international-cross-country-half-marathon-run-2026":
                "https://malaysiarunner.com/event/68/Serian%20Eco%20Run%205.0%202026%20%28Early%20Bird%29",
            "youth-day-limbang-motor-day-2026":
                "https://limbang.sarawak.gov.my/web/subpage/news_view/941",
        })
        by_id = {e["id"]: e for e in self.events}
        self.assertIsNone(by_id["kuching-international-cat-festival-2026"]["official_url"])
        self.assertIsNone(by_id["kejohanan-muaythai-piala-premier-sarawak-edisi-ke-10-2026"]["official_url"])
        self.assertIsNone(by_id["karnival-siburan-2026"]["official_url"])
        self.assertIsNone(by_id["karnival-balau-dalat-2026"]["official_url"])
        self.assertEqual(
            by_id["santubong-international-trail-run-2026"]["official_url"],
            "https://www.santubongtrail.com/",
        )
        self.assertIsNone(by_id["santubong-international-trail-run-2026"].get("info_url"))
        kept = {
            "pata-travel-mart-ptm-2026": "https://www.pata.org/pata-travel-mart-2026",
            "wak-festival-2026-wak-kuching-2026": "https://wakfestival.com/",
            "padawan-raft-safari-2026": "https://borneoraftsafari.com/events/padawan-raft-safari-2026",
            "sarawak-international-dragon-boat-regatta-2026": "https://regatta.sarawaktourism.com/",
            "kuching-waterfront-festival-2026": "https://regatta.sarawaktourism.com/",
            "sarawak-regatta-2026": "https://regatta.sarawaktourism.com/",
            "borneo-jazz-festival-2026": "https://jazzborneo.com/",
            "santubong-international-trail-run-2026": "https://www.santubongtrail.com/",
        }
        for eid, url in kept.items():
            self.assertEqual(by_id[eid]["official_url"], url)
            self.assertIsNone(by_id[eid].get("info_url"))
        for eid in (
            "limbang-open-international-tug-of-war-2026",
            "countdown-2027-2026",
            "pesta-baeuh-kedayan-se-borneo-peringkat-daerah-lawas-m-t-k-l-2026",
            "serian-international-remote-control-carnival-2026",
            "sarikei-unity-run-8-0-2026",
        ):
            self.assertIsNone(by_id[eid].get("info_url"))
            self.assertIsNone(by_id[eid]["official_url"])
        self.assertEqual(by_id["baram-basin-indigenous-cultural-festival-bbic-festival-2026"]["status"], "cancelled")
        self.assertEqual(by_id["karnival-balau-and-agrofest-dalat-2026"]["status"], "cancelled")
        self.assertNotIn("krian-nature-marathon-1st-edition-2026", by_id)


class Validation(unittest.TestCase):
    def bad(self, **kw):
        ev = dict(GOOD, **kw)
        return L.validate_event(ev)

    def test_good(self):
        self.assertEqual(L.validate_event(GOOD), [])

    def test_rejects(self):
        self.assertTrue(self.bad(summary="Call " + "012-" + "345 6789 now."))
        self.assertTrue(self.bad(summary="Email a" + "@" + "example.com."))
        self.assertTrue(self.bad(summary="One. Two. Three."))
        self.assertTrue(self.bad(summary="x" * 300))
        self.assertTrue(self.bad(division="Atlantis"))
        self.assertTrue(self.bad(event_type="gala"))
        self.assertTrue(self.bad(event_type="race"))
        self.assertTrue(self.bad(event_type="regatta"))
        self.assertTrue(self.bad(event_type=""))
        self.assertTrue(self.bad(status="live"))
        self.assertTrue(self.bad(end_date="2026-11-01"))
        self.assertTrue(self.bad(start_date=None))
        self.assertTrue(self.bad(month=10))
        self.assertTrue(self.bad(official_url="http://insecure.example"))
        self.assertTrue(self.bad(info_url="http://insecure.example"))
        self.assertTrue(self.bad(id="Not A Slug"))
        self.assertTrue(self.bad(phone="012"))
        ev = dict(GOOD); del ev["source_url"]
        self.assertTrue(L.validate_event(ev))

    def test_tbc_allows_no_date(self):
        self.assertEqual(self.bad(start_date=None, end_date=None, date_tbc=True), [])

    def test_event_type_allows_null_and_known_values(self):
        self.assertEqual(self.bad(event_type=None), [])
        for kind in L.EVENT_TYPES:
            self.assertEqual(self.bad(event_type=kind), [], kind)

    def test_slug(self):
        self.assertEqual(L.make_id("Pesta Ba'euh Kedayan", 2026), "pesta-baeuh-kedayan-2026")
        self.assertEqual(L.make_id("WAK Festival 2026", 2026), "wak-festival-2026")

    def test_info_url_optional(self):
        self.assertEqual(self.bad(info_url=None), [])
        ev = dict(GOOD)
        ev.pop("info_url", None)
        self.assertEqual(L.validate_event(ev), [])
        self.assertEqual(self.bad(info_url="https://example.com/story"), [])


class Rendering(unittest.TestCase):
    def setUp(self):
        self.html = build.render_index(build.load_events())
        self.about = build.render_about(build.load_events())

    def test_no_contacts_or_internal_fields_rendered(self):
        for page in (self.html, self.about):
            self.assertNotIn("Organiser", page)
            self.assertNotIn("Contact", page)
            self.assertNotIn("contact: to be confirmed", page.lower())
            self.assertIsNone(L.PHONE_RE.search(re.sub(r"<script.*?</script>", "", page, flags=re.S)))
            self.assertNotIn("mtcp.sarawak.gov.my", page)
            self.assertNotIn("discovered_at", page)
            self.assertNotIn("2026-10-15T00:00", page)

    def test_no_source_attribution_copy(self):
        for page in (self.html, self.about):
            low = page.lower()
            self.assertNotIn("calendar of tourism events", low)
            self.assertNotIn("source:", low)
            self.assertNotIn("sarawak tourism calendar", low)

    def test_unpublished_not_rendered(self):
        evs = [dict(GOOD), dict(GOOD, id="hidden-2026", name="Hidden Thing", status="pending")]
        self.assertEqual([e["id"] for e in L.public(evs)], ["test-fest-2026"])
        self.assertNotIn("source_url", L.public(evs)[0])

    def test_official_url_link(self):
        card = build.render_card(dict(GOOD, official_url="https://testfest.example"))
        self.assertIn('class="event-link" href="https://testfest.example"', card)
        self.assertIn(f">{GOOD["name"]}</a>", card)
        self.assertNotIn("Official site", card)
        self.assertNotIn("More information", card)
        self.assertNotIn("event-links", card)

    def test_info_url_link(self):
        card = build.render_card(dict(GOOD, info_url="https://example.com/story"))
        self.assertIn('class="event-link" href="https://example.com/story"', card)
        self.assertNotIn("More information", card)
        self.assertNotIn("Official site", card)
        self.assertNotIn("Suara", card)
        self.assertNotIn("Borneo Post", card)
        both = build.render_card(dict(
            GOOD,
            official_url="https://organiser.example/event",
            info_url="https://example.com/story",
        ))
        self.assertIn('href="https://organiser.example/event"', both)
        self.assertNotIn("example.com/story", both)
        self.assertNotIn("Official site", both)
        self.assertNotIn("More information", both)
        plain = build.render_card(GOOD)
        self.assertNotIn("event-link", plain)


class Pipeline(unittest.TestCase):
    def test_enqueue_new_pending(self):
        queue, rep = q.enqueue(manifest(cand()), L.load(L.EVENTS), [])
        self.assertEqual(rep["pending"], ["kuching-lantern-walk-2026"])
        self.assertEqual(queue[0]["status"], "pending")
        self.assertEqual(queue[0]["source_url"], "https://dayakdaily.com/lantern")
        self.assertEqual(L.validate_event(queue[0]), [])

    def test_enqueue_dedupes_seed(self):
        c = cand(name="Sarawak Regatta", start_date="2026-10-31", end_date="2026-11-01", month=10)
        _, rep = q.enqueue(manifest(c), L.load(L.EVENTS), [])
        self.assertEqual(rep["duplicate"], [{"id": "sarawak-regatta-2026", "of": "sarawak-regatta-2026"}])
        c2 = cand(name="Kuching Marathon", start_date="2026-09-27", month=9, url="https://x.example/km")
        _, rep = q.enqueue(manifest(c2), L.load(L.EVENTS), [])
        self.assertEqual(len(rep["duplicate"]), 1)

    def test_enqueue_dedupes_within_queue(self):
        queue, _ = q.enqueue(manifest(cand()), [], [])
        queue, rep = q.enqueue(manifest(cand(url="https://other.example/x")), [], queue)
        self.assertEqual(len(queue), 1)
        self.assertEqual(len(rep["duplicate"]), 1)

    def test_enqueue_rejects_bad_manifest_and_candidates(self):
        with self.assertRaises(ValueError):
            q.enqueue({"candidates": []}, [], [])
        _, rep = q.enqueue(manifest(cand(summary="Call " + "019-" + "000 0000.")), [], [])
        self.assertEqual(len(rep["invalid"]), 1)

    def test_publish_moves_only_approved(self):
        queue, _ = q.enqueue(manifest(cand(), cand(name="Miri Kite Day", url="https://y.example/k", town="Miri", division="Miri")), [], [])
        publish.set_status(queue, ["kuching-lantern-walk-2026"], "approved")
        events, rest, ids = publish.publish(copy.deepcopy(L.load(L.EVENTS)), queue)
        self.assertEqual(ids, ["kuching-lantern-walk-2026"])
        self.assertEqual(len(events), 115)
        self.assertEqual([r["id"] for r in rest], ["miri-kite-day-2026"])
        self.assertEqual(next(e for e in events if e["id"] == ids[0])["status"], "published")

    def test_candidate_schema_file_matches_queue_requirements(self):
        schema = json.loads((ROOT / "automation" / "candidate.schema.json").read_text())
        req = schema["$defs"]["candidate"]["required"]
        self.assertEqual(sorted(req), sorted(q.MANIFEST_REQUIRED))
        self.assertEqual(sorted(schema["$defs"]["candidate"]["properties"]["division"]["enum"]), sorted(L.DIVISIONS))

    def test_sources_are_https(self):
        for s in json.loads((ROOT / "data" / "sources.json").read_text()):
            self.assertTrue(s["url"].startswith("https://"), s)
