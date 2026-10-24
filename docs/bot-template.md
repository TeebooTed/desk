# Bot template: how a Grok Bot sets up Desk end to end

Paste the README's "Set up Desk" prompt into your bot, or follow these steps yourself.

## 1. Install (on the user's computer)
- Public repo: `curl -fsSL https://raw.githubusercontent.com/TeebooTed/desk/main/install.sh | bash`
- Private fork: `gh repo clone OWNER/desk && cd desk && ./install.sh` (the curl install only works for public repos).
- This creates `~/Desk`, installs the local relay (`relay/desk-relay.py`, 127.0.0.1:8765) with autostart (LaunchAgent `local.desk-relay` on macOS, systemd user unit `desk-relay.service` on Linux), builds `index.html` and opens it.

## 2. Connect the page to the bot
1. Create a **webhook routine** named "Desk messages" (step 4). Copy its URL and key.
2. The user opens Desk → gear → pastes URL + key → Save → Send test. The key is stored only in `~/.config/desk-relay/config.json` (0600). Never write it in the page, status.json, live.json, layout.json or a repo.

## 3. Routine A: twice-daily refresh (schedule, e.g. 7:00 and 13:00 local)
Prompt outline:
- Write `~/Desk/status.json` (areas → projects; see docs/data-format.md).
- Write `~/Desk/live.json`: `fetched`, `events`, `due`, `waiting`, `unread`, `bot_name`, `routines`, `teammates`, `activity`, `approvals` in `waiting`, `replies`, and optional `widgets` (docs/widgets.md).
- Keep `replies` from earlier runs that are newer than 3 days.
- Run `python3 ~/Desk/build.py ~/Desk/status.json`.
- Do not touch `layout.json` unless the user asked for a layout change (docs/layout.md).

## 4. Routine B: "Desk messages" (webhook)
Handles messages the page sends. Each starts with a tag:
- `[Desk setup]`: first-run answers; build status.json from them.
- `[Desk ask] …`: answer it; append `{"q","a","at"}` to `live.json` `replies` and rebuild.
- `[Desk routine] <pause|resume|run-now> <name>`: do it, update `routines`, rebuild.
- `[Desk approval] <id> <Approve|Reject|Edit: …>`: act on the approval, remove it from `waiting`, rebuild.
- `[Desk · Waiting on you] …`: record the decision, remove the item, rebuild.
- `[Desk layout] …` (optional): edit `~/Desk/layout.json` per docs/layout.md (bump `updated`), rebuild.

See docs/routines.md for full prompts.

## 5. Verify
`curl -s 127.0.0.1:8765/health` returns ok; Send test reaches the bot; after a refresh the page shows today's date in the footer.
