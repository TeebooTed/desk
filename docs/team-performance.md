# Team performance

A small, file-based way to measure how your agents are doing against their goals, help them improve one change at a
time, and see it on Desk's **Teammates** panel. Nothing is fabricated: a KPI with no data shows "no data yet".

```
team-perf/
  RULE_GENERAL.md     the general self-improvement rule every agent follows
  agents.json         YOUR team: goals, tasks, KPIs, levers, review schedule   (git-ignored; start from the example)
  agents/<name>.md    per-agent rule files, generated from agents.json          (git-ignored)
  log/<name>.jsonl    append-only run logs written by the agents                (git-ignored)
  auto/<name>.jsonl   optional measurements written by your own checkers        (git-ignored)
  improvements.json   optional open improvement items                           (git-ignored)
  routines.json       optional recurring jobs per agent and their status        (git-ignored)
  log-run             helper that appends one log line
  incident            optional helper for an append-only incident log (open / close / summary)
examples/team-perf/   a clearly-labelled EXAMPLE team (Assistant, Researcher, Writer, Designer, Ops) used by the demo
tools/team_perf.py    collector: reads team-perf/ and writes data/team_perf.json for build.py
```

## 1. Configure your agents
Copy the example and edit it:

```sh
cp examples/team-perf/agents.json team-perf/agents.json
```

Each agent:

```json
{"name": "Writer", "role": "Copy & newsletters", "goal": "Ship drafts the owner approves with few edits.",
 "tasks": [{"id": "newsletter", "name": "Newsletter draft", "cadence": "Weekly"}],
 "kpis": [{"id": "approved_first", "label": "Drafts approved without rework", "target": 80, "dir": ">=", "unit": "%", "source": "self", "from": "log"},
          {"id": "minutes", "label": "Minutes per draft", "target": 30, "dir": "<=", "unit": "min", "source": "self", "from": "log"}],
 "levers": ["draft template", "self-edit checklist"]}
```

- `name` should match the agent's name in `live.json` → `teammates`, so the score lands on the right card.
- Mark one agent `"lead": true` (your main bot). It gets its own card even if it isn't a listed teammate, and runs the weekly review.
- **KPIs**: 3-5 per agent, a mix of effectiveness (on time, correct, accepted) and efficiency (minutes, retries, corrections).
  `dir` is `>=` (higher is better) or `<=` (lower is better). `unit` `%` for booleans averaged to a percentage, `/wk` for counts per week.
- `source`: `self` (the agent logs it) or `auto` (a script you run writes it to `team-perf/auto/<name>.jsonl`, same line format).
- `levers`: the things the agent may change on its own while improving. Everything else is a proposal to the lead.
- `review`: the self-review, team review and monthly target review cadence shown on the panel.

Then generate each agent's rule file and give it to the agent together with `RULE_GENERAL.md`:

```sh
python3 tools/team_perf.py --write-rules
```

## 2. Logging
After every run of a recurring task (including failed or skipped runs) the agent appends one line:

```sh
team-perf/log-run Writer newsletter ok --min 32 --kpi approved_first=true --kpi minutes=32 --note "sent for approval"
team-perf/log-run Writer newsletter ok --improve "Add a self-edit checklist" --improve-kpi approved_first   # start a trial change
```

Logs are append-only; corrections are new lines. Use `null` for anything not measured. No secrets in logs.
Auto measurements (for example an uptime checker) append `{"ts": "...", "agent": "Ops", "outcome": "ok", "kpi": {"uptime": true}}`
to `team-perf/auto/<name>.jsonl`.

## 3. Scoring
- Each KPI: 0-100 against its target (capped at 100) over the last 7 days; the 28-day value is shown alongside.
- Agent score: the mean of the KPIs that have data. **Green** ≥ 90, **amber** ≥ 70, **red** < 70.
  **Grey / "Limited data"** when fewer than half of the KPIs have data.
- Sparkline: the daily average of run outcomes (ok 1, partial 0.5, fail 0) for 28 days; the last 7 days are shaded.

## 4. Build
Run the collector before the build (your refresh routine can do both):

```sh
python3 tools/team_perf.py && python3 build.py
```

`build.py` reads `data/team_perf.json` (`$DESK_TEAMPERF` overrides) and warns if it is more than 13 hours old.
In demo mode (`example-status.json`, no data file) it builds the example team on the fly.
At small and medium section sizes each teammate shows a coloured dot and score; click it for the details.
At large and full size the details show on each card.

## 5. The weekly review
Suggested routines for your bot (adjust the times):
- **Every run**: the agent logs it.
- **Weekly self-review** (e.g. Fridays): each agent sends the lead its KPIs vs target (7 and 28 days), what went wrong, and one change it made or proposes.
- **Weekly team review** (e.g. Mondays): the lead runs `tools/team_perf.py`, reads every agent's card, keeps or reverts trial changes
  (keep only if the KPI improved and nothing else got worse), updates `improvements.json`, and reports to you.
- **Monthly**: the lead reviews KPI targets and replaces any KPI that doesn't reflect the goal.

Self-improvement never widens permissions: see the hard limits in `team-perf/RULE_GENERAL.md`.

## Incidents (optional)
`team-perf/incident --service myapp open|close|update|list|summary|current` keeps an append-only incident log in
`team-perf/incidents/<service>.jsonl`, handy for an uptime or "minutes down" KPI.

Test: `python3 tools/test_teamperf.py` (Playwright, example data).
