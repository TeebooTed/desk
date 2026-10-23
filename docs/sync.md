# Syncing Desk between computers

Desk keeps small page state in the local helper so every computer can share it:
layout, project pins/priorities, collapsed panels, theme, approval drafts, "waiting on you"
answers, pending tile edits and **widget storage** (`desk-wstore:<id>`).
Webhook settings (`desk-hook`) and the webhook key are never synced.

## How it works

* The page wraps `localStorage` for those keys. Every write is stamped (ms timestamp) and
  POSTed to the helper's `/state`; the page pulls `/state` on load, on focus and every 20 s.
  If something changed elsewhere it reloads once you are idle (not editing, not typing).
* The helper stores `$DESK_DIR/state.json` as `{key: {v, t, d}}` and merges **last writer
  wins per key** (newest `t`, ties broken by device name, `v: null` = deleted). A winning
  `desk-layout` is also written to `layout.json`.
* Browser-only values from older versions are migrated on first load with `t = 1`, so a real
  edit on any computer always beats them.
* `localStorage` is only a cache; the helper copy is the source of truth.

## Moving state between computers

The helper only listens on `127.0.0.1`. Two transports, both private:

1. **Peer pull (recommended, needs a private network such as Tailscale).** Create
   `~/.config/desk-relay/sync.json` on each computer (mode 600):

   ```json
   {"token": "<same long random string on every computer>",
    "peers": ["https://other-computer.your-tailnet.ts.net:8443"]}
   ```

   Expose the helper to your tailnet only, e.g. `tailscale serve --bg --https=8443 http://127.0.0.1:8765`
   (never Tailscale Funnel). Each helper pulls `GET /sync/state` from its peers every 30 s;
   that endpoint requires the `X-Desk-Sync: <token>` header and refuses browser requests.
2. **Relay by your bot (no network setup).** Anything that can run commands on both computers
   can sync them: `GET /state` on one, `POST /state {"keys": ...}` on the other, and back.
   Merging is idempotent, so running it often is safe.

```sh
curl -s -H 'X-Desk: 1' http://127.0.0.1:8765/state            # read
curl -s -H 'X-Desk: 1' -X POST http://127.0.0.1:8765/state \
     -d '{"keys": {"desk-theme": {"v": "dark", "t": 1767225600000}}}'   # merge
```
