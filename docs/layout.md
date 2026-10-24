# layout.json: customizing Desk's layout

Desk's arrangement (section order, sizes, visibility, per-section options, appearance) lives in `~/Desk/layout.json`.
People edit it from the page (pencil button or **E**); bots can edit the file directly.

## How it loads and saves
1. `build.py` validates `layout.json` (or `$DESK_LAYOUT`, or `layout.default.json` if missing) and embeds it in `index.html` (`<script id="layout">`).
2. The page also keeps a copy in localStorage (`desk-layout`). Whichever has the newer `updated` wins.
3. On load the page asks the relay (`GET http://127.0.0.1:8765/layout`) and applies that copy if it is newer.
4. Every change is saved after 500 ms to localStorage and `POST /layout`. The relay writes `layout.json` atomically and keeps the previous one as `layout.prev.json`. If the relay is down, the page shows "Saved in this browser only" and retries every 30 s.
5. `index.html?reset-layout` resets to the default (undo still works in that session).

**After a bot edits layout.json, set `updated` to the current ISO time and rebuild** (`python3 ~/Desk/build.py ~/Desk/status.json`), or the page's newer local copy wins.

## Schema (version 1)
```json
{
 "version": 1,
 "updated": "2026-10-23T20:00:00Z",
 "updated_by": "bot",
 "sections": [
  {"id": "today", "visible": true, "size": "m", "days": 2},
  {"id": "waiting", "visible": true, "size": "m"},
  {"id": "projects", "visible": true, "size": "full",
   "fields": {"progress": true, "next": true, "owner": true, "legend": true},
   "sort": "priority", "default_filter": "all", "area_order": ["work", "personal"]},
  {"id": "tiles", "visible": true, "size": "full", "labels": true,
   "order": ["Mail", "Calendar"], "hidden": ["News"], "extra": [{"label": "Wiki", "url": "https://example.com"}]},
  {"id": "routines", "visible": true, "size": "full", "show": "all"}
 ],
 "phone": {"order": ["today", "waiting", "projects"]},
 "appearance": {"accent": "#2f6fed", "density": "cozy", "font_scale": 100, "radius": 14, "columns": 0},
 "theme": "auto"
}
```
- Section ids: `setup, today, waiting, ask, tiles, widgets, frame, podsta, projects, teammates, activity, routsum, routines`. `frame` is Picture Frame and `podsta` is Podsta (both built in, size `s` by default; see [widgets.md](widgets.md#built-in-pod-widgets)). Array order = screen order. Missing sections are appended with defaults; unknown ids are dropped.
- `size`: `s` (1/3), `m` (1/2), `l` (2/3), `full`, on a 12-column grid. On phones every section is full width.
- `phone.order`: separate order for screens under 700 px (empty = same as desktop).
- `today.days` 1–3; `routines.show` `all|failed`; `projects.sort` `priority|name|progress|status`; `projects.default_filter` `all` or a status.
- `appearance`: `accent` `#rrggbb` or `""` (default blue); `density` `compact|cozy|roomy`; `font_scale` 90–125; `radius` 0–24 px; `columns` 0 (auto) to 5 area columns. `theme` `auto|light|dark`.
- Out-of-range values are clamped (in both build.py and the page).

## Verbs for bots
When the user asks for a layout change (in chat or via a `[Desk layout]` message), map it to an edit:

| verb | edit |
|---|---|
| move X to top / above Y | reorder `sections` (or `phone.order` if they said phone) |
| hide X / show X | `visible: false/true` |
| resize X | `size: s|m|l|full` |
| accent | `appearance.accent` |
| density / bigger text | `appearance.density`, `appearance.font_scale` |
| fewer columns | `appearance.columns` |
| dark mode | `theme` |

Then set `updated`/`updated_by` and rebuild.

## In the page
- **Edit mode** (pencil or **E**): each section shows a handle ⋮⋮, size chip, hide 👁 and ⚙ settings. Drag, or focus the handle and press Space, arrows, Space (Esc cancels). Moves are announced to screen readers.
- Edit bar: Undo/Redo (Ctrl/Cmd+Z, Shift for redo, 50 steps), Appearance, + Add section (hidden sections), Reset, Export, Import, Done.
