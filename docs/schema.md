# Event schema (v1)

One schema for every event, whatever the source. It is enforced by
`scripts/events_lib.py` (`validate_event`, `validate_collection`), checked by
`scripts/validate.py`, `scripts/build.py` (build fails on any error) and
`tests/test_schema.py`.

Files that hold schema records:

- `data/events.json`: the published listing (`status` is `published`, or `cancelled` which is kept but not rendered).
- `data/review-queue.json`: candidates waiting for review (`pending`, `approved`, `rejected`, `duplicate`).

## Public fields (rendered)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | slug | yes | Lowercase `a-z0-9-`, unique. `make_id(name, year)` appends the year unless the name already ends with it, for example `kuching-marathon-2026`. |
| `name` | string | yes | Event name as the organiser or source states it. |
| `start_date` | `YYYY-MM-DD` or null | unless `date_tbc` | First day. |
| `end_date` | `YYYY-MM-DD` or null | no | Last day, null for one-day events. Must be on or after `start_date`. |
| `date_tbc` | bool | yes | `true` when no fixed date is known. The card shows **TBC** and the event sorts last in its month. |
| `month` | int 1-12 | yes | The tab the event lists under. Equals the month of `start_date` when a date is known. |
| `venue` | string or null | no | Null renders as "{town} (venue to be confirmed)". |
| `town` | string | yes | |
| `division` | enum | yes | One of the 12 divisions: Betong, Bintulu, Kapit, Kuching, Limbang, Miri, Mukah, Samarahan, Sarikei, Serian, Sibu, Sri Aman. |
| `summary` | string | yes | Short and factual, 1-2 sentences, at most 280 characters, original wording. |
| `event_type` | enum or null | no | One of `festival`, `sports`, `concert`, `cultural`. Rendered as the red label on the card. Null or omitted renders no label. Any other value, including the retired `race` and `regatta`, is a validation error. |
| `official_url` | https URL or null | no | The organiser's own event page. When set, it is the card's click-through destination (whole card is the control; no separate link label). A news article is not an official site. |
| `info_url` | https URL or null | no | A dedicated article about this event. Used as the card destination only when `official_url` is null. Null or omitted when there is no such article. No outlet name is shown on the card. An official Facebook or Instagram post/page about the event is allowed here or as `official_url` (same source-link rule). |

## Internal fields (never rendered)

| Field | Required | Notes |
|---|---|---|
| `source_url` | yes | https page the facts were verified on. |
| `source_name` | yes | Human label for that source. |
| `discovered_at` | yes | ISO 8601 with offset (MYT). |
| `status` | yes | `pending`, `approved`, `rejected`, `duplicate`, `published`, `cancelled`. |
| `review_note` | no | Reviewer caveats, for example "Venue/organiser matched by layout". |

`build.py` renders only `status == "published"` and passes only the public
fields to the templates (`events_lib.public`).

## Hard rules

- **No phone numbers, emails or organiser contact lines** in any field, public or internal. The validator rejects Malaysian phone shapes and email addresses. Cards carry no organiser or contact line at all.
- **Source-linked listing (Oct–Dec 2026, for now):** a published event whose `start_date` falls in **2026-10-01 .. 2026-12-31** must have at least one of `official_url` or `info_url` pointing at an official site, social media post/page, or news article about the event. Seed calendars (for example MTCP) alone are not enough. Events in that window without such a link must not stay `published` — set `status` to `cancelled` (same pattern as BBIC). Do not invent URLs. Prefer news or dedicated official pages over INTOURCAMS listing URLs. This window can be widened later without changing the link rule itself. **Weekly scan:** Maintainer Bot’s Monday run also looks for new sourced events for **present and future** dates in the scan period (not past-only backfill by default) — cadence in `docs/runbook.md`.
- No unknown fields: anything outside the two tables is a validation error.
- `event_type` is a closed list: `festival`, `sports`, `concert`, `cultural`. `festival` covers a pesta, fest, fair, carnival, fiesta, or regatta. For now every published regatta is `festival`, including ones the ministry or the Tourism Board also describe as boat races. `sports` covers a race, marathon, run, trail, championship, tournament or games. Sarawak Tourism Board uses "sports" and "sports tourism" for marathons, so `race` is not a separate value. `concert` is a concert. `cultural` is a ritual, parade, open house or other cultural programme. The Board's public section is [Culture](https://www.sarawaktourism.com/web/things-to-do/thing-view/culture), and the ministry calls the Gawai Dayak Open House a cultural event. "Heritage" and "arts" are not a clearer single label: heritage is used for places, and arts does not fit rituals.
- No on-site source attribution. `source_url` and `source_name` exist for review only.
- Every URL is https.

## Seed

The first 114 events were seeded from the Sarawak 2026 Calendar of Tourism
Events using `scripts/migrate_seed.py` (one-off). Phone, email, organiser and
website fields were dropped, and contact details were stripped from notes, which
became `review_note`. The seed is just a starting set. Discovery
(`docs/automation.md`) adds events from all sources in the same schema.
