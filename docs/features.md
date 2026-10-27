# Desk features: filters, stamps, machines, palette, alerts

Everything here works with the example data (`python3 build.py`) and with your own `status.json` / `live.json`.
All of it is plain HTML/CSS/JS built into `index.html`; nothing loads from the internet.

## Org (area) filter

A row of chips above Projects: **All** plus one chip per area (from `area_order`). Click a chip to show one area,
Shift-click to combine areas. The choice is saved in the browser (`localStorage`, key `desk-org`).
The filter also applies to **Today**, **Waiting on you**, approvals and the header counts, using each item's
`area` field (items without an area always show). Colours come from the area's position: `--org-1` … `--org-4`
in `custom/features.css`; edit those to pick your own. A chip can carry a tooltip from `org_tips` in status.json:

```json
"org_tips": {"Work": "Day job", "Side": "Weekend project"}
```

Calendar events can be mapped to areas with `cal_org` (calendar name → area).

## "As of" stamps

Each section shows when its data was last fetched ("As of 9:40 AM · 12 min ago"). Old data turns amber, very old
data turns red, and missing numbers show "—" instead of a misleading 0. The header pill summarizes the oldest panel.
If `live.json` is older than `live_stale_hours` (default 13) the build writes a `LIVE_STALE` marker so your refresh
routine can notice.

## Machines panel

One card per computer: online / asleep / offline, last seen, disk use (amber at 80%, red at 90% by default),
local services up/down, and an optional pinned note. Machine classes decide how loud a card gets:
`always_on` (goes red when it disappears), `sleeper` (laptops: asleep is normal, never red) and `retiring`.

Data comes from `data/machines_health.json`, written by `tools/machines_health.py` from your config
(`data/machines_config.json`, start from `examples/machines/machines_config.example.json`) and your bot's machine list.
`data/` is git-ignored. In demo mode Desk uses `examples/machines/machines_health.example.json`.
For live disk and service numbers from a Mac, see the optional [heartbeat](heartbeat.md).

## Command palette (⌘K / Ctrl+K)

Search projects, agents, machines and actions from the keyboard (for example "run a routine now" or "filter by area").
Arrow keys to move, Enter to open, Esc to close.

## Alerts banner

A short list at the top of the page for things that need you: failed routines, machines that went quiet or are low on
disk, stale data. Each alert can be snoozed for 4 hours or until 8 AM tomorrow (saved in this browser only; `B2CFG.snoozeH` in
`custom/alerts.js` sets the hours).

## Refresh history

Inside **Routines**, the last few refresh runs are listed with which files they updated, so a run that skipped the
live panels stands out. Desk reads this from the backups your refresh routine leaves next to `status.json`
(`status.pre-refresh-*.json` / `live.pre-refresh-*.json`), or from `DESK_REFRESH_BACKUPS`.

## Approval cards

Waiting items with `kind: "draft"` or `"post"` show the preview and Approve / Edit / Decline. Choosing sends a message
only, `[Desk approval] <id> <answer>` with `area: "approval"`, through the local relay on 127.0.0.1:8765.
Desk never posts or sends anything itself; your bot acts on the message.

## Teammate badges

Teammate cards get a small badge showing how recently that agent logged progress (`desk-log`): green within 24 hours,
amber within 72, grey after that. Build.py collects it into `team_activity` from `updates.jsonl`.

## Tests

```sh
python3 tools/test_features.py   # Playwright browser test on example data
sh tools/test_scan.sh            # the safety scan must stop a build with planted secrets
```
