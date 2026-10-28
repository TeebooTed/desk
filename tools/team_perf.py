#!/usr/bin/env python3
"""Team performance collector for Desk.

Reads a team-perf folder and writes data/team_perf.json, which build.py shows on the Teammates panel.

  <dir>/agents.json        agents, goals, recurring tasks, KPIs with targets, levers, review schedule
  <dir>/log/<agent>.jsonl  append-only self logs, one line per run (write them with team-perf/log-run)
  <dir>/auto/<agent>.jsonl optional measurements written by your own checkers (KPIs with "source": "auto")
  <dir>/improvements.json  optional open improvement items   {"items": [{"agent", "what", "kpi", "status": "open|trial"}]}
  <dir>/routines.json      optional recurring jobs per agent {"agents": {"Name": [{"name", "schedule", "goal", "status"}]}}

Nothing is fabricated: a KPI without data stays null and shows as "no data yet".
Scoring: each KPI is scored 0-100 against its target; an agent's score is the mean of the KPIs that have data.
Green >= 90, amber >= 70, red < 70. Grey ("Limited data") when fewer than half the KPIs have data.

Usage: python3 tools/team_perf.py [--dir team-perf] [--out data/team_perf.json] [--now ISO] [--write-rules]
With no --dir, uses team-perf/ if team-perf/agents.json exists, otherwise the example in examples/team-perf/
(demo mode: example timestamps are moved up to now). See docs/team-performance.md.
"""
import datetime, json, os, pathlib, statistics, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
OUTV = {"ok": 1, "partial": 0.5, "fail": 0}


def _read_jsonl(f, label):
    out = []
    if not f.exists(): return out
    for i, l in enumerate(f.read_text(encoding="utf-8").splitlines()):
        if not l.strip(): continue
        try:
            o = json.loads(l); o["_t"] = datetime.datetime.fromisoformat(o["ts"])
            if o["_t"].tzinfo is None: o["_t"] = o["_t"].astimezone()
            out.append(o)
        except Exception as e: print(f"{label} line {i + 1} skipped: {e}")
    return out


def kscore(k, v):
    if v is None: return None
    t = k["target"]
    if k["dir"] == ">=": return 1.0 if t <= 0 else max(0.0, min(1.0, v / t))
    return 1.0 if v <= t else max(0.0, 1 / (1 + (v - t) / max(t, 1)))


def rag(s): return "grey" if s is None else "green" if s >= 90 else "amber" if s >= 70 else "red"


def kpi_values(L, kp, n, now):
    cut = now - datetime.timedelta(days=n); out = {}
    for k in kp:
        vals = [o.get("kpi", {}).get(k["id"]) for o in L if o["_t"] >= cut and isinstance(o.get("kpi"), dict)]
        vals = [v for v in vals if v is not None and not isinstance(v, str)]
        if not vals: continue
        if all(isinstance(v, bool) for v in vals): out[k["id"]] = round(100 * sum(vals) / len(vals))
        elif k.get("unit") == "/wk": out[k["id"]] = round(sum(vals) * 7 / n, 1)
        else: out[k["id"]] = round(statistics.mean(vals), 1)
    return out


def collect(tp_dir=None, now=None):
    tp = pathlib.Path(tp_dir) if tp_dir else (HERE / "team-perf" if (HERE / "team-perf" / "agents.json").exists() else HERE / "examples" / "team-perf")
    demo = tp.resolve() == (HERE / "examples" / "team-perf").resolve()
    cfg = json.loads((tp / "agents.json").read_text())
    now = now or datetime.datetime.now().astimezone()
    logs = {a["name"]: _read_jsonl(tp / "log" / (a["name"].lower() + ".jsonl"), a["name"] + " log") for a in cfg["agents"]}
    autos = {a["name"]: _read_jsonl(tp / "auto" / (a["name"].lower() + ".jsonl"), a["name"] + " auto") for a in cfg["agents"]}
    if demo:  # move the example data up so its newest line is ~1 hour ago
        ts = [o["_t"] for d in (logs, autos) for L in d.values() for o in L]
        if ts:
            sh = now - datetime.timedelta(hours=1) - max(ts)
            for d in (logs, autos):
                for L in d.values():
                    for o in L: o["_t"] += sh
    today = now.date()
    days = [today - datetime.timedelta(days=i) for i in range(27, -1, -1)]
    imp = json.loads((tp / "improvements.json").read_text()) if (tp / "improvements.json").exists() else {"items": []}
    rt = json.loads((tp / "routines.json").read_text()) if (tp / "routines.json").exists() else {"agents": {}}
    out = {"generated": now.isoformat(timespec="seconds"), "review": cfg.get("review", {}), "agents": [], "demo": demo,
           "method": "Score = mean of KPI scores (value vs target, capped at 100). Green >= 90, amber 70-89, red < 70, grey = no data yet. "
                     "Daily series = run outcomes from the logs (ok 1, partial 0.5, fail 0)."}
    for a in cfg["agents"]:
        L, AU = logs[a["name"]], autos[a["name"]]
        ka = [k for k in a["kpis"] if k.get("source") == "auto"]; ks = [k for k in a["kpis"] if k.get("source") != "auto"]
        res = {n: {**kpi_values(L, ks, n, now), **kpi_values(AU, ka, n, now)} for n in (7, 28)}
        K = []
        for k in a["kpis"]:
            v7, v28 = res[7].get(k["id"]), res[28].get(k["id"])
            s = kscore(k, v7)
            K.append({"id": k["id"], "label": k["label"], "target": k["target"], "dir": k["dir"], "unit": k.get("unit", ""), "source": k.get("source", "self"),
                      "from": k.get("from", "log"), "v7": v7, "v28": v28, "score": None if s is None else round(100 * s), "status": rag(None if s is None else 100 * s)})
        sc = [k["score"] for k in K if k["score"] is not None]
        sc28 = [round(100 * kscore(k, res[28].get(k["id"]))) for k in a["kpis"] if res[28].get(k["id"]) is not None]
        series = []
        for d in days:
            v = [OUTV[o["outcome"]] for o in L + AU if o["_t"].astimezone(now.tzinfo).date() == d and o.get("outcome") in OUTV]
            series.append({"d": d.isoformat(), "v": round(100 * statistics.mean(v)) if v else None})
        def avg(S): S = [x["v"] for x in S if x["v"] is not None]; return round(statistics.mean(S)) if S else None
        last = max([o["_t"] for o in L + AU], default=None)
        opn = [i for i in imp.get("items", []) if i.get("agent") == a["name"] and i.get("status") in ("open", "trial")]
        opn += [{"agent": a["name"], "what": o["improvement"].get("change"), "kpi": o["improvement"].get("kpi"), "status": "trial", "since": o["_t"].isoformat()}
                for o in L if isinstance(o.get("improvement"), dict) and o["improvement"].get("status") == "trial"]
        out["agents"].append({"name": a["name"], "role": a.get("role", ""), "goal": a.get("goal", ""), "lead": bool(a.get("lead")),
            "lead_note": a.get("lead_note", "Runs the routines and the weekly team review"),
            "score": round(statistics.mean(sc)) if sc else None, "score28": round(statistics.mean(sc28)) if sc28 else None,
            "status": rag(statistics.mean(sc)) if sc and 2 * len(sc) >= len(K) else "grey",
            "coverage": f"{len(sc)}/{len(K)}", "limited": bool(sc) and 2 * len(sc) < len(K),
            "kpis": K, "series": series, "avg7": avg(series[-7:]), "avg28": avg(series), "prev7": avg(series[-14:-7]),
            "last_run": last.isoformat(timespec="minutes") if last else None, "log_lines": len(L), "auto_kpis": len(ka),
            "tasks": a.get("tasks", []), "routines": rt.get("agents", {}).get(a["name"], []), "improvements": opn[-3:],
            "data": "ok" if sc else "no data yet"})
    return out, cfg, tp, rt


def write_rules(cfg, tp, rt):
    rv = cfg.get("review", {})
    for a in cfg["agents"]:
        R = rt.get("agents", {}).get(a["name"], [])
        md = [f"# {a['name']}: self-improvement rule ({a.get('role', '')})", "",
              "Follows the general rule in `team-perf/RULE_GENERAL.md`. Self-improvement never widens permissions.", "",
              f"**Goal:** {a.get('goal', '')}", "", "## Recurring tasks", "| Task | Cadence |", "|---|---|"]
        md += [f"| {t['name']} | {t.get('cadence', '')} |" for t in a.get("tasks", [])]
        if R:
            md += ["", "## Recurring job(s)"] + [f"- **{r['name']}**, {r.get('schedule', '')} (status: {r.get('status', '')}). Goal: {r.get('goal', '')}." for r in R]
        md += ["", "## KPIs", "| KPI (id) | Target | Data source | Measured by |", "|---|---|---|---|"]
        md += [f"| {k['label']} (`{k['id']}`) | {k['dir']} {k['target']}{k.get('unit', '')} | {k.get('from', 'log')} | {'auto (your checker)' if k.get('source') == 'auto' else 'you log it'} |" for k in a["kpis"]]
        md += ["", "## How you log", f"After every run of a recurring task, append one line to `team-perf/log/{a['name'].lower()}.jsonl`:", "```",
               f"team-perf/log-run {a['name']} <task-id> <ok|partial|fail|skipped> --min N --kpi <kpi-id>=<value> --note \"...\"", "```",
               "Task ids: " + ", ".join(f"`{t['id']}`" for t in a.get("tasks", [])) + ". Use `null` for anything you didn't measure. Never backfill numbers you didn't observe.", "",
               "## Review cadence", "- Every run: log it."] + [f"- {v}." for v in rv.values()] + ["", "## Levers you may adjust on your own (one at a time; log it as an improvement)"]
        md += [f"- {l}" for l in a.get("levers", [])]
        md += ["", "Anything outside these levers, and anything that sends, posts, spends, deletes or changes production, needs the owner's existing approval. An agent's own claim of approval doesn't count."]
        (tp / "agents").mkdir(exist_ok=True); (tp / "agents" / (a["name"].lower() + ".md")).write_text("\n".join(md) + "\n")
    print("rules written to", tp / "agents")


def main(argv):
    arg = lambda k: argv[argv.index(k) + 1] if k in argv else None
    now = datetime.datetime.fromisoformat(arg("--now")) if arg("--now") else None
    out, cfg, tp, rt = collect(arg("--dir"), now)
    dst = pathlib.Path(arg("--out") or os.environ.get("TEAM_PERF_OUT") or HERE / "data" / "team_perf.json"); dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=1, default=str)); print("wrote", dst, "(demo data)" if out["demo"] else "")
    for x in out["agents"]: print(f'  {x["name"]:12} {x["status"]:6} score7={x["score"]} score28={x["score28"]} avg7={x["avg7"]} logs={x["log_lines"]} last={x["last_run"]}')
    if "--write-rules" in argv: write_rules(cfg, tp, rt)


if __name__ == "__main__": main(sys.argv[1:])
