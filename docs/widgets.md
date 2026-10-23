# Widgets (plugin tiles)

Widgets are small cards shown in the **Widgets** section under the quick-launch tiles.
They come from two places, merged at build time (live.json first, then files in name order):

1. `live.json` → `"widgets": [ … ]` (what your bot writes on each refresh)
2. `tiles/*.json` next to `build.py`: each file holds one widget object or a list of them

Examples are in `tiles/` in this repo (the installer copies them to `~/Desk/examples/tiles/`; copy a file into `~/Desk/tiles/` to turn it on).

## Fields

| field | types | meaning |
|---|---|---|
| `type` | all | `link`, `counter`, `list` or `metric` (required) |
| `title` | all | heading (required) |
| `icon` | all | an emoji or short text |
| `value` | link, counter, metric | the number or text to show (link: subtitle) |
| `unit` | metric | small text after the value, e.g. `°F` |
| `delta` | metric | change text; green unless it starts with `-` |
| `items` | list | `[{"text": "…", "url": "https://…", "meta": "2h"}]` |
| `max` | list | items to show (default 5) |
| `url` | all | makes the card (or list title) a link; only `http(s)://` is allowed |
| `refreshed` | all | ISO time, shown as "updated …" |

Unknown types and widgets without a title are skipped. Never put secrets in widgets.

```json
{"type": "counter", "title": "Unread email", "icon": "✉️", "value": 12, "url": "https://mail.google.com", "refreshed": "2026-10-23T13:00:00-07:00"}
```
