# Logging your progress to Desk

Desk shows each project as a card. You can update your cards yourself with `desk-log`.
Your note shows up on the card ("Updated 2m ago by Scout") and at the top of its Recent list.

## When to log
- You finished a meaningful step (a deploy, a draft delivered, a check passed).
- You got **blocked**, or you got **unblocked**.
- The project is **done**.

Don't log every small action. A few entries a day per project is plenty.

## How
```
./desk-log --agent <YourName> --project <project-id> --note "One plain sentence." \
    [--percent 0-100] [--status active|blocked|on_hold|done] [--next-step "Short next step"]
```
Example:
```
./desk-log --agent Scout --project website-refresh --note "Homepage draft approved" --percent 80
```
- `--note`: one sentence in plain words, what happened. No jargon dumps, no logs, no links to private files.
- `--percent`, `--status` and `--next-step` are optional. Only set them when they changed.
- You can't change priority. the person who owns the Desk sets that.
- Time defaults to now (local time; set DESK_TZ to override). Don't edit `updates.jsonl` by hand. It's append-only, and the tool locks it for you.

## Finding the project id
```
./desk-log --list              # all projects: id, area, status, name
./desk-log --list --area Work   # areas come from your status.json
```
If you mistype an id, the tool prints the closest matches and exits with an error. Nothing is logged.

## A project that isn't on Desk yet
```
./desk-log --agent <YourName> --new "Project name" --area Work --note "Why it matters, one sentence"
```
This only *proposes* the project. Your bot reviews it and adds it to Desk. Don't log progress to it until it has an id.

## Never log
Secrets, passwords, API keys, tokens, codes, email addresses, phone numbers, card numbers, or anyone's private data.
The tool rejects obvious ones, but that's a backstop. Keep notes clean yourself.

## When it shows up
Run `./desk-watch --ensure` once: it rebuilds Desk at most once every 2 minutes after a new entry, then runs
`DESK_DEPLOY_CMD` if you set one (e.g. `cp "$DESK_INDEX" ~/Desk/index.html`), or leaves a `PENDING_DEPLOY` flag for
your bot's refresh routine to deploy. Agents on other machines need a shared filesystem (or a bot that logs for them).
