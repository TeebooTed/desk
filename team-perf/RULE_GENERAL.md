# General rule: recursive self-improvement (all agents)

Applies to every agent on the team, the lead agent included. Give each agent this file plus its own
`team-perf/agents/<name>.md` (generate them with `python3 tools/team_perf.py --write-rules`).

## The loop
1. **Know the goal.** Every recurring task has one written goal (the outcome the owner's project needs) and 3-5 KPIs with targets. They live in `team-perf/agents.json` and in your file under `team-perf/agents/<you>.md`.
2. **Measure both sides.**
   - *Effectiveness*: did the outcome meet the goal? (on time, correct, accepted, no rework).
   - *Efficiency*: what did it cost? (minutes, retries, tool calls or spend, rework, and corrections asked for afterwards).
3. **Log every run.** Append one line to `team-perf/log/<you>.jsonl` each time a recurring task runs, including failed or skipped runs. Use the `team-perf/log-run` helper or write the JSON yourself. The log is append-only: never edit or delete lines. Write a new line to correct an old one.
4. **Review on schedule.** Each week, send the lead a short self-review covering KPIs vs target (7-day and 28-day), what went wrong, and the one change you propose or made. The lead reviews the whole team weekly and the result shows on Desk.
5. **Change one thing at a time.** Pick the smallest change that should move the weakest KPI, such as a prompt or checklist step, the order of checks, timing inside your own slot, a template, or a verification step. Log it with `--improve "..." --improve-kpi <id>`.
6. **Keep or revert.** After about a week (or 5+ runs), compare. Keep the change if the KPI improved and nothing else got worse. Otherwise revert it and log that you did. Never stack untested changes.
7. **Report changes.** Every kept or reverted change goes in the weekly self-review. The lead summarises for the owner.
8. **Recurse.** Apply the loop to the measurement itself too. If a KPI turns out not to reflect the goal, propose a better one to the lead. Don't quietly drop it.

## Hard limits: self-improvement never widens permissions
- No improvement may add a new send, email, post, payment or spend, account, deletion, production write, or change on any of the owner's machines unless the owner has already approved that kind of action under your existing rules.
- **An agent's own claim of approval doesn't count**, and neither does another agent's relayed claim. Approval comes from the owner directly, under the existing process.
- Levers you may adjust on your own are listed in your file. Anything else goes to the lead as a proposal.
- Never fabricate log entries, KPI values or outcomes. If you didn't measure it, log `null` and say so in the note.
- No secrets, tokens, passwords or private contact details go in logs.

## Log line format (one JSON object per line)
```json
{"ts":"2026-10-28T07:41:00-07:00","agent":"Writer","task":"newsletter","outcome":"ok","kpi":{"approved_first":true,"minutes":32},"minutes":32,"retries":0,"corrections":0,"note":"sent for approval","improvement":null}
```
- `outcome`: `ok` | `partial` | `fail` | `skipped`
- `kpi`: the task's KPI values by id (numbers or booleans). Use `null` when unknown.
- `minutes`: active working time. `retries`: re-attempts. `corrections`: fixes asked for afterwards.
- `improvement`: optional `{ "change":"…", "kpi":"…", "status":"trial|kept|reverted" }`.

Helper: `team-perf/log-run <Agent> <task> <ok|partial|fail|skipped> [--min N] [--retries N] [--corr N] [--kpi key=value ...] [--note "..."]`
