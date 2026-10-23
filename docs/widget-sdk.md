# Desk widget SDK

Widgets are small third-party web apps that show up as sections on your Desk. Every widget runs in a locked-down sandbox. It only sees the data you allow on the consent screen.

## Package layout

```
my-widget/
  manifest.json   required
  index.html      entry (name set by manifest.entry)
  app.js, style.css, icon.svg …   optional bundled files
```

Limits: 40 files, 256 KB per file, 1 MB per package. Allowed file types are `.html .js .css .json .svg .png .jpg .jpeg .gif .webp .txt .md`. Paths must be relative, with no `..` and no leading `/`.

### manifest.json

| field | required | notes |
|---|---|---|
| `id` | yes | `^[a-z0-9][a-z0-9-]{1,40}$`. The layout section id becomes `w:<id>`. |
| `name`, `version` | yes | Changing the version shows the update flow. |
| `author`, `homepage`, `description` | – | Shown on the consent screen. |
| `entry` | – | Defaults to `index.html`. |
| `size` | – | `{default: "s"\|"m"\|"l"\|"full", height: 40–900}` |
| `permissions` | – | Scopes, listed below. Anything not listed is denied. |
| `network` | if `network` | 1–5 `https://` origins on public hostnames. No IPs, no localhost. |
| `refresh` | – | Seconds (≥ 60) between `refresh` events. |
| `sha256` | recommended | Map of `file → hex sha256`. Desk checks every file before it installs. |

`tools/widget_pack.py <dir>` fills in `sha256`, writes `<id>.zip` and prints the manifest hash. Gallery and URL installs use that hash as a pin.

## Scopes

| scope | gives the widget |
|---|---|
| `theme` | `getData("theme")` (`light`/`dark`, accent) plus a `theme` event when it changes |
| `time` | `getData("time")`: the time zone and current ISO time |
| `storage` | `storage.get/set`: a private 64 KB key/value store, kept in this browser |
| `network` | `fetch()` to the origins listed in `manifest.network` only |
| `projects.summary` | Counts per area and status, with no project names |
| `calendar.today` | Today's events (time + title) |
| `unread.counts` | Unread counts per inbox |

## Bridge API

Desk injects a tiny SDK into every widget as `window.desk`, so you never handle the raw `postMessage` protocol:

```js
await desk.ready();
const t = await desk.getData("theme");        // throws "permission_denied" if not granted
await desk.storage.set("note", "hi");          // needs "storage"
desk.on("theme", t => document.body.dataset.theme = t.mode);
desk.on("refresh", load);                      // every manifest.refresh seconds
desk.setHeight(document.body.scrollHeight);
desk.openLink("https://example.com");          // user confirms
```

Under the hood, messages are `{desk:1, tok, id, method, params}`. `tok` is a random per-frame token that Desk checks along with `event.source`.

Methods:
- `ready`
- `getData(scope)` → data, or the error `permission_denied` / `unknown_scope`
- `setHeight(px)` (40–900)
- `openLink(url)` (http/https only; Desk asks the user to confirm and opens it with `noopener`)
- `storage.get(key)` and `storage.set(key, value)`
- `bot.send` (reserved; currently returns `not_available`)

Events: `theme`, `refresh`. Desk accepts at most 40 calls per second from each widget.

## Installing

Click **Edit layout → ＋ Widget**. There are three ways to install:
- **From URL**: point it at a `manifest.json` (optionally `#sha256=<hash>`).
- **From zip or folder.**
- **From the gallery** (`registry.json`). Bundled entries work offline.

The consent screen shows the author, every permission in plain words and every network origin. Nothing is granted until you approve, and you can untick any permission.

**Updates:** a new version shows a NEW badge for any permission it adds and asks again. **Disable** keeps the files but stops the frame. **Remove** deletes the files, the grants and the stored data.

Installed packages live in the helper's `widgets/` directory (`GET/POST/DELETE /widgets`). The next build embeds them, so they also work without the helper.

## Threat model

**Assets:** your Desk data (projects, calendar, inbox counts, approvals), the helper (it can message your bot), the helper's webhook secret, and your other browser sessions.

**Attacker:** a widget author, or whoever compromises a widget's hosting.

**Isolation**
- Each widget runs in `<iframe sandbox="allow-scripts" srcdoc>`, which gives it an opaque origin.
  - It cannot touch the Desk DOM, Desk's localStorage, cookies or its own storage. It cannot open popups, submit forms or navigate the top window.
  - The frame also has `referrerpolicy=no-referrer` and `allow=""` (no camera, microphone, geolocation and so on).
- A CSP is injected as the first element:
  - `default-src 'none'`; scripts only with a per-render nonce, so there is no `eval` and no remote script.
  - `connect-src` lists only the granted origins.
  - `img-src` allows `data:`, `blob:` and the granted origins.
  - `form-action` and `base-uri` are `'none'`.
  - Meta refresh is stripped.
- Bundled JS, CSS and SVG files are inlined, and nothing else loads.

**Bridge**
- Desk only accepts a message whose `event.source` is that widget's own frame and whose random per-frame token matches.
- Data scopes are checked against the grants on every call. Results are copies of minimal summaries; `projects.summary` contains no names.
- `openLink` needs your confirmation.

**Helper**
- Every request except a preflight must carry the `X-Desk: 1` header. That forces a CORS preflight, so a sandboxed widget or another website can't trigger `/send` or `/widgets` with a simple request.
- The helper validates every package: id and path regex, extension allowlist, size caps and a realpath guard. It writes atomically.
- The webhook secret never leaves the helper and is never put into the page, `live.json` or the repo.

**Integrity:** per-file `sha256` and manifest pins are checked with WebCrypto before the consent screen appears.

**Known limitations**
- If a widget navigates its own frame, it could leak data it was already granted once, through the URL. Desk re-renders the frame with a new token. After 5 unexpected loads in 10 s, Desk disables the widget.
- DNS prefetch hints can't be fully blocked by CSP.
- Widget storage is per browser and is not synced.
- URL and gallery installs over `raw.githubusercontent.com` need the repo to be public. Bundled gallery entries always work.
- A widget you grant `network` to can send what it sees to its declared origins. Only grant data scopes and network together to authors you trust.
