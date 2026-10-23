# Desk status file format

`build.py` reads a JSON file (default `example-status.json`) and inlines it into
`template.html` to produce `index.html`. Top-level object:

| Field | Type | Req. | Notes |
|---|---|---|---|
| `generated` | string (ISO 8601) | optional | Shown in the footer as "Status data". |
| `areas` | object | **required** | Keys are area ids; values are arrays of projects. |

## Areas

Each key of `areas` (e.g. `"Work"`) is shown as a card. Display names come from
the `AREAS` map in `template.html`
(`AREAS={Work:"Work",Side:"Side project",Personal:"Personal"}`); a key missing
from `AREAS` is shown as-is. Edit `AREAS` to rename or reorder areas.

## Project

| Field | Type | Req. | Notes |
|---|---|---|---|
| `name` | string | **required** | Unique within its area (used as the key for local priority pins). |
| `status` | string | **required** | `active`, `blocked`, `hold` or `done`. Drives colour and the filter tabs. |
| `percent` | number 0-100 | recommended | Progress bar and area average. |
| `next_step` | string | recommended | Shown under the progress bar and in the pop-up. |
| `priority` | string | optional | `high`, `medium` or `low` (P1/P2/P3). Clicking the pin overrides it locally in the browser. |
| `owner` | string | optional | Who is doing it. |
| `last_update` | string (YYYY-MM-DD) | optional | |
| `summary` | string | optional | Pop-up: Summary. |
| `in_progress` | string | optional | Pop-up: In progress. |
| `waiting_on` | string | optional | Pop-up: highlighted "Waiting on" box. |
| `recent` | array of strings | optional | Pop-up: Recent list, newest first. |
| `links` | array of `{label, url}` | optional | Pop-up: Links. Both strings. |
| `unverified` | boolean | optional | `true` marks numbers as "est." (estimate). `verified: false`, or the word `UNVERIFIED` anywhere in the project, does the same. `build.py` also sets it when a `*.md` table next to the status file has `UNVERIFIED` in its third column for a similarly named row. |

The pop-up (click a project) shows all the optional text fields above, plus a
"Message bot about this" box that sends `{source, area, project, status,
message, sent_at}` through the local relay (see `routines.md`).

## Tiles

Launch tiles are not in the status file; edit the `TILES` array in
`template.html`:

| Field | Type | Req. | Notes |
|---|---|---|---|
| `label` | string | **required** | Text under the icon. |
| `url` | string | **required** | Opened on click. |
| `letter` | string | **required** | Monogram shown in the icon. |
| `color` | string (CSS colour) | **required** | Icon background. |
| `badge` | string | optional | Small badge, e.g. `"1"`. |
| `serif` | boolean | optional | Serif monogram. |

## Example

```json
{
  "generated": "2026-01-15T16:00:00Z",
  "areas": {
    "Work": [
      {
        "name": "Website refresh",
        "status": "active",
        "percent": 60,
        "priority": "high",
        "next_step": "Review homepage draft",
        "owner": "Example Agent",
        "last_update": "2026-01-15",
        "summary": "Refresh the marketing site.",
        "in_progress": "Homepage and pricing page drafted.",
        "recent": ["2026-01-14: draft homepage ready"],
        "waiting_on": "Design sign-off",
        "links": [{"label": "example.com", "url": "https://example.com/"}]
      }
    ],
    "Personal": [
      {"name": "Plan trip", "status": "done", "percent": 100, "next_step": "None"}
    ]
  }
}
```

See `example-status.json` for a full sample.


# live.json (today strip, waiting, unread, routines, replies)

`build.py` also inlines `live.json` (next to `build.py`; override with env
`DESK_LIVE`). If neither `live.json` nor a status-file argument is given it uses
`example-live.json` (demo). Every field is optional. **Never put webhook URLs,
tokens or other secrets in this file**: the page is plain HTML.

| Field | Type | Notes |
|---|---|---|
| `fetched` | ISO 8601 | When the bot last wrote this file. |
| `bot_name` | string | Shown on buttons ("Ask Sam…"). Default "your bot". |
| `user_name` | string | Greeting ("Good morning, Sam"). |
| `events` | array of `{title, start, end?, cal?, url?}` | Calendar items; today + tomorrow are shown. ISO times with offset. |
| `due` | array of `{title, at, area?}` | Deadlines, shown in the Today strip. |
| `waiting` | array of `{id, q, opts[], ctx?, note?}` or approvals (below) | Decisions the bot needs. Keep `id` stable; the page remembers answers per id. Answers arrive as `area:"waiting"`, `decision_id`, `answer`. |
| `unread` | object `{tileLabel: count}` | Badge on mail tiles (`letter:"M"`) whose `label` matches. |
| `routines` | array, see below | Routine panel (collapsible, under projects). Hidden when empty. |
| `teammates` | array of `{name, role?, doing?, waiting_on?, updated?, on_hold?}` | Collapsible card grid, one per agent. Leave `doing` empty if unknown. |
| `activity` | array of `{at, what, kind, link?}` | `kind`: `send`, `deploy`, `edit`, `post` or `other`. Only today's entries are shown, newest first. |
| `replies` | array of `{at, text, q?, from?}` | Answers to `[Desk ask]` messages; newest 3 shown under the Ask box. Keep ~10. |

### Approvals (inside `waiting`)

An item with `kind: "draft"` or `kind: "post"` appears under **Approvals**
instead of as a question: `{id, kind, q (title), preview (the text), to?, ctx?}`.
Buttons send `[Desk approval] <id> Approve|Reject|Edit: <changes>` with
`area:"approval"`, `approval_id`, `answer`, `kind`. Remove the item once handled.

### Routine object

| Field | Type | Notes |
|---|---|---|
| `name` | string | **required**; also used in button messages. |
| `schedule` | string | Human text, e.g. "Weekdays 9 AM & 4 PM". |
| `trigger` | `schedule` \| `event` \| `webhook` | Non-schedule triggers get a tag. |
| `paused` | boolean | Shows Resume instead of Pause. |
| `next_run` | ISO 8601 or null | |
| `last_run` | ISO 8601, `YYYY-MM-DD`, or null | |
| `last_status` | `ok` \| `failed` \| null | `failed` rows are highlighted, sorted first, and open the panel automatically. |

## First-run setup

If `status.json` is missing or has no projects, Desk shows a **Welcome** card.
Its button sends a `[Desk setup]` message (`area:"setup"`) through the helper,
and **Copy request** copies the same text for pasting into chat. A bot that
receives it should write `status.json` and `live.json` as specified above, then
run `python3 build.py status.json`.

### Sample prompt to paste into your bot

```text
Set up my Desk dashboard (https://github.com/TeebooTed/desk). Read
docs/data-format.md, then in ~/Desk:
1. Write status.json: my current projects grouped by area (Work, Side,
   Personal or areas you suggest), each with name, status, percent, priority,
   summary, next_step and links. Mark guesses "unverified": true.
2. Write live.json with events (my calendars, today and tomorrow), due,
   waiting (decisions you need from me, with 2-3 short answer options),
   unread (unread count per inbox, using my tile labels), routines (all my
   routines with schedule, next/last run, status, paused) and replies: [].
3. Edit TILES and AREAS in template.html to match my inboxes and areas.
4. Run: python3 ~/Desk/build.py ~/Desk/status.json
5. Create a twice-daily "Desk progress refresh" routine that repeats 1, 2, 4,
   and a webhook "Desk messages" routine as in docs/routines.md.
No secrets in any of these files.
```
