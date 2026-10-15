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
| `event_type` | enum or null | no | One of `festival`, `race`, `regatta`, `concert`, `cultural`, `sports`. Rendered as the red label on the card. Null or omitted renders no label. Any other value is a validation error. |
| `official_url` | https URL or null | no | The organiser's own event page. Rendered as an "Official site" link. |

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
- No unknown fields: anything outside the two tables is a validation error.
- `event_type` is a closed list taken from words the site already uses (festivals, races, regattas, concerts, cultural events, sports). `festival` also covers a pesta, fest, fair, carnival or fiesta. A race, marathon, run or trail is `race`. A regatta or regata is `regatta`. A concert is `concert`. A ritual, parade, open house or other cultural programme that is not already one of those is `cultural`. A championship, tournament, games or other sports meeting that is not a race or regatta is `sports`.
- No on-site source attribution. `source_url` and `source_name` exist for review only.
- Every URL is https.

## Seed

The first 114 events were seeded from the Sarawak 2026 Calendar of Tourism
Events using `scripts/migrate_seed.py` (one-off). Phone, email, organiser and
website fields were dropped, and contact details were stripped from notes, which
became `review_note`. The seed is just a starting set. Discovery
(`docs/automation.md`) adds events from all sources in the same schema.
