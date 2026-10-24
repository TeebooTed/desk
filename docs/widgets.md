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

## Built-in pod widgets

Desk works best if you have a SOLID Pod. Two built-in sections read straight from your pod with your own sign-in. They are separate layout sections (`frame` and `podsta`), so you can move, resize or hide them in edit mode. Both only ever send `GET` requests: they never upload, change, move or delete anything, and they never like, comment or post.

Without a pod (local mode) each one shows a short explanation, leading with "Desk works best if you have a SOLID Pod.", and a **Set up my pod** button. If you picked *Don't ask again*, they stay hidden. In pod mode while signed out they offer **Sign in**.

Settings live in this browser (`localStorage` key `desk-podw`) and are changed with the ⚙︎ button on each widget.

### Picture Frame

*Your own photos, quietly on rotation.* Cycles the photos in a folder of your pod, with a gentle crossfade.

| Setting | Default | Notes |
|---|---|---|
| Folder | `photos/` | Relative to your pod. Must stay inside your pod (`..` and other sites are refused). |
| Include subfolders | off | Up to 3 levels deep. |
| Shuffle | off | |
| Change every | 30 seconds | 10 s to 15 min. |

- Shows `.jpg .jpeg .png .webp .gif .avif`, and `.heic/.heif` where the browser can display them (others are skipped quietly). Other files are ignored.
- Photos are fetched with your signed-in session as blobs and shown from object URLs. Only the photo on screen and the next one are fetched; object URLs are revoked as soon as they're no longer needed.
- Hover to pause. Click (or Enter) to open the photo full size; Esc or a click closes it.
- Empty or missing folder: "Your photos folder is empty for now. Add a few pictures to it in your pod, and they'll start showing up here."

### Podsta

*Recent posts from people you follow.* Cycles through recent posts from the people you follow on [Podsta](https://teebooted.github.io/Podsta/), newest first, with the author's name and picture, the text, the first photo, the time, and an **Open in Podsta** link (`https://teebooted.github.io/Podsta/post?url=<post>`).

Where it reads (Podsta's own layout, nothing Desk-specific):

| What | Where |
|---|---|
| Who you follow | `<your pod>/podsta/contacts/friends.ttl` (`foaf:knows`, `foaf:name`, `schema:image`, `schema:url` per friend) |
| A friend's public posts | `<their pod>/podsta/public-index.ttl` |
| Posts shared with their contacts | `<their pod>/podsta/contacts-index.ttl` (readable only by people in their `podsta/contacts/group.ttl#contacts`) |

- **Privacy:** Desk shows only what each friend's pod server returns to you. "Only me" posts are never in an index, and a contacts index you're not allowed to read is skipped. Contacts-only posts carry a small *Contacts* badge.
- On Community Solid Server, membership in a friend's contacts group is checked by reading `group.ttl` anonymously, so their contacts-only posts reach you only if that file is publicly readable.
- **Limits:** up to 20 people and the latest 5 posts each. Each pod gets 8 seconds; a slow pod is skipped with a short note ("…'s pod didn't answer in time. Showing everyone else.").
- **Caching:** results are kept for 5 minutes, then refreshed in the background. **Check for new posts** in the settings refreshes now.
- Your sign-in is only sent to your own pod and to the pod of the friend being read. Anything hosted elsewhere is fetched anonymously.
- Setting: **Next post every** (default 20 seconds). Hover pauses; ‹ › step through.
- Nothing yet: "Nothing new from the people you follow yet. Once they post, you'll see it here. Follow a few more people in Podsta to keep things lively."

Art for both (and the pod welcome card) is in `assets/widgets/`, in light and dark versions.
