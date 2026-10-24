# Desk with a Solid pod (optional)

Desk works **with or without** a [Solid](https://solidproject.org/) pod.

- **This computer (default).** Same as always: `build.py` bakes your status JSON into `index.html`, agents run `desk-log` to add to `updates.jsonl`, and nothing leaves your machine. If you never open the Storage setting, nothing changes. No pod code is loaded and nothing is written to localStorage.
- **Solid pod.** Desk reads your projects and updates from a pod you control. Agents write their progress there with their own credentials, and you can give each one access to only the areas it works on.

## Why use a pod?

- **One copy, many devices.** Your laptop, phone, and agents running elsewhere all read and write the same data. You don't need to sync files.
- **You own it.** The pod can be self-hosted, such as the Community Solid Server on your own box, or run by any provider. Desk talks standard Solid (LDP + WAC), so you can switch providers without changing Desk.
- **Fine-grained agent access.** Each area folder has its own access rule. An agent that only works on "Side project" can be granted that folder and nothing else.

## Folder layout

Desk keeps everything under a single folder in your pod, `grokbot/` by default. You can change it in settings. Each area gets its own subfolder:

```
<pod>/grokbot/
  meta.json                 # area order, labels, area->folder map, time zone (schema "desk-pod/1")
  .acl                      # owner-only
  work/
    status.json             # {"area": "Work", "label": "Work", "projects": [ ... same project objects as status.json ... ]}
    updates/                # one JSON file per update (same fields as a line of updates.jsonl)
    .acl                    # owner-only by default; add agents per area
  side-project/
    status.json
    updates/
    .acl
  personal/
    ...
```

Both modes use the same data format. Projects are the objects from [data-format.md](data-format.md), and each update file holds exactly one `updates.jsonl` entry. Desk merges them with the same rules as `build.py`: notes, `percent`, `next_step`, status, the 12-note cap, and so on.

### Area to folder mapping (data-driven)

The folder for an area is chosen in this order:

1. `area_folders` in the pod's `meta.json`;
2. `area_folders` in your local status JSON, for example:
   ```json
   "area_folders": { "Side": "side-project" }
   ```
3. otherwise a slug of the area key (`Work` → `work/`, `Personal` → `personal/`).

When Desk reads the pod, each folder's `status.json` records which area it holds (`"area"`), so you can also rename folders without breaking anything. Just keep `area` the same.

## Setup

### 1. Get a pod

**Self-hosted, Community Solid Server (CSS):**

```bash
npx @solid/community-server@7 -p 3000 -c @css:config/file.json -f ~/solid-data
```

Open `http://localhost:3000/`, create an account, and create a pod (for example `you`). Your pod URL will be `http://localhost:3000/you/`.

**Any provider.** Any Solid server that supports WAC or ACP works. Use the pod URL it gives you. If its sign-in (OIDC issuer) is on a different host than the pod, enter that host under **Sign-in server**.

### 2. Open Desk over http

Solid sign-in redirects back to the page, so Desk must be opened over http(s), not `file://`. The local relay serves Desk at:

```
http://127.0.0.1:8765/app/
```

The relay only serves `index.html` and `assets/`, and it checks the `Host` and `Origin` headers. If you open `index.html` as a file while in pod mode, Desk shows your local data with a notice telling you to use the address above.

### 3. Turn on pod mode

Open ⚙︎ settings and find **Storage**:

1. Choose **Solid pod**.
2. Enter your **Pod URL**. The **Desk folder in the pod** defaults to `grokbot/`.
3. Click **Sign in** and approve Desk at your pod's sign-in page.

These settings are kept in this browser's localStorage (`desk-storage`). They never go into build files.

### 4. Connect existing folders and create missing ones

Click **Scan pod**. Desk lists the chosen folder and shows:

- **✓ connected**: area folders that already exist, matched by folder name or slug. Desk uses them as they are.
- **missing — create**: a checkbox for each area on this computer that has no folder yet.

![Connect/create step](img/solid-pod-connect.png)

Check the ones you want and click **Copy my Desk into my pod**. With **Copy this computer's projects into the new folders** checked, each new folder's `status.json` is filled with that area's projects from this computer. Otherwise it starts empty.

Desk **only creates what's missing**:

- Every write uses `If-None-Match: *`, so an existing file is never overwritten.
- Nothing is ever deleted.
- Each new folder gets an **owner-only** `.acl` (only your WebID can read, write, or control it).
- On ACP servers, which use `.acr`, folders inherit the pod's private default instead.

**New areas later.** Once `meta.json` exists, any area you add on this computer automatically gets its own folder, created the next time Desk reads the pod.

![Pod mode](img/solid-pod-mode.png)

The pill in the bottom-left shows the state:

- **green**: reading the pod (with the time of the last read and **Refresh**);
- **amber**: not signed in or nothing set up yet;
- **red**: fallback.

Desk re-reads the pod every 60 seconds and when the tab becomes visible again. Changed cards are briefly outlined.

### Fallback: never a blank page

If sign-in fails, the pod server is unreachable, a request times out, or the pod URL is wrong, Desk shows **this computer's data** with a clear notice and a **Retry** button. Switching Storage back to **This computer** returns to exactly the normal local behavior.

## Agents: client credentials and per-area access

Agents don't sign in through a browser. They use **client credentials** (an ID and secret tied to a WebID).

**On CSS:** sign in at `<server>/.account/`, open **Client credentials**, pick the WebID the agent should act as, and create a token. Give the agent its own WebID (a separate account or pod) so you can grant it only certain areas. Other providers have a similar page.

Put the credentials in an env file that never goes in any repo, and `chmod 600` it:

```bash
# ~/.config/desk/agent-two.env
DESK_POD_URL=https://pod.example.org/you/
DESK_POD_ROOT=grokbot/            # default
DESK_POD_ISSUER=https://pod.example.org/   # default: the pod's server
DESK_POD_CLIENT_ID=...
DESK_POD_CLIENT_SECRET=...
DESK_POD_AREAS=side-project       # optional: the folders this agent may use
```

Then:

```bash
desk-log --pod ~/.config/desk/agent-two.env --list
desk-log --pod ~/.config/desk/agent-two.env --project podcast-backlog --percent 55 --note "Recorded two episodes" --agent "Agent Two"
# or: export DESK_POD_ENV=~/.config/desk/agent-two.env
```

`desk-log --pod`:

- reads the projects from the area folders it can see;
- finds the project's area;
- writes the update as a new file in **that area's** `updates/` folder.

It uses DPoP-bound tokens when the Python `cryptography` package is installed, and plain Bearer tokens otherwise. Without `--pod`, `desk-log` works exactly as before.

### Granting an agent one area

Every area folder's `.acl` is owner-only by default. To let an agent write to just `side-project/`, add a rule to `grokbot/side-project/.acl`. You can do this with any Solid file browser (such as Penny or mashlib), or with a PUT:

```turtle
@prefix acl: <http://www.w3.org/ns/auth/acl#>.

<#owner> a acl:Authorization; acl:agent <https://pod.example.org/you/profile/card#me>;
  acl:accessTo <./>; acl:default <./>;
  acl:mode acl:Read, acl:Write, acl:Control.

<#agent-two> a acl:Authorization; acl:agent <https://pod.example.org/agent-two/profile/card#me>;
  acl:accessTo <./>; acl:default <./>;
  acl:mode acl:Read, acl:Append.
```

- `acl:Append` is enough for `desk-log` to add updates.
- Give `acl:Write` too if the agent should also edit `status.json`.
- Because the agent can't list the root folder, set `DESK_POD_AREAS=side-project` in its env file.

An agent without a grant on an area gets "403" from the pod and simply doesn't see that area's projects.

## Moving data between modes

- **Into the pod:** use **Scan pod** → **Copy my Desk into my pod** (above).
- **Out of the pod:** click **Export from pod** in settings. Desk downloads `status.json` and `updates.jsonl` in the normal local format. Put them next to `build.py` and run:
  ```bash
  python3 build.py status.json
  ```
  The result is the same cards you saw in pod mode, and plain `desk-log` keeps working on the exported files.

## For developers

- The Solid sign-in library (Inrupt's `@inrupt/solid-client-authn-browser`, MIT) is pre-bundled as `assets/solid-auth.js`. It is loaded only in pod mode. To rebuild it:
  ```bash
  cd tools/solid && npm install && node build.mjs
  ```
- Storage lives in one small layer in `template.html`, `window.DeskStore`, with two backends that share the same interface: load status and areas, load updates, append an update, and save status. The `local` backend is the data baked in by `build.py`. The `pod` backend implements the same interface on top of the pod's area folders.
