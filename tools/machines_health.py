#!/usr/bin/env python3
"""machines_health: write data/machines_health.json for Desk's Machines panel. Box-side, read-only, no secrets.

Inputs (all optional except the config):
  --config data/machines_config.json   machines, services/ports, thresholds, static snapshots (ports are config, not code).
                                       Example: examples/machines/machines_config.example.json
  --list FILE      your bot's machine list saved as JSON ({"machines":[{machineId,label,kind,connected}]}). Your refresh
                   routine asks the bot for it and saves the result.
  --probe FILE     optional one-off probe results {machineId: {"at": ISO, "disk_pct": int, "ports": {"8765": "up"|"down"}}}
                   (from a one-off check you ran yourself).
State: data/machines_state.json keeps last_seen per machine (Desk records it itself: the time of the last poll with
connected=true) and a missed-poll counter for debounce. Output: data/machines_health.json. Never writes IPs or process args.
"""
import argparse, datetime, json, pathlib, shutil, zoneinfo
TZ = datetime.datetime.now().astimezone().tzinfo
D = pathlib.Path(__file__).resolve().parent.parent / "data"
RANK = {"grey": 0, "green": 1, "yellow": 2, "red": 3}
def worst(*ls): return max([l for l in ls if l] or ["grey"], key=lambda l: RANK[l])
def iso(d): return d.astimezone(TZ).replace(microsecond=0).isoformat() if d else None
def parse(s):
    try: return datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception: return None
def jload(p, d):
    try: return json.loads(pathlib.Path(p).read_text())
    except Exception: return d
def disk_level(p, t):
    if p is None: return "grey"
    return "red" if p >= t["disk_red"] else "yellow" if p >= t["disk_yellow"] else "green"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(D / "machines_config.json")); ap.add_argument("--list"); ap.add_argument("--probe")
    ap.add_argument("--state", default=str(D / "machines_state.json")); ap.add_argument("--out", default=str(D / "machines_health.json"))
    a = ap.parse_args()
    cfg = json.loads(pathlib.Path(a.config).read_text()); t = cfg["thresholds"]
    now = datetime.datetime.now(TZ)
    lm = jload(a.list, None) if a.list else None
    listed = {m.get("machineId"): m for m in (lm or {}).get("machines", [])} if lm else None
    probe = jload(a.probe, {}) if a.probe else {}
    st = jload(a.state, {})
    rows = []
    for m in cfg["machines"]:
        s = st.setdefault(m["id"], {})
        L = listed.get(m["id"]) if listed is not None else None
        conn = None if listed is None or L is None else bool(L.get("connected"))
        if conn: s["last_seen"] = iso(now); s["missed"] = 0
        elif conn is False: s["missed"] = int(s.get("missed", 0)) + 1
        seen = parse(s.get("last_seen")); age = (now - seen).total_seconds() / 60 if seen else None
        if conn is None: state, lvl = "unknown", "grey"
        elif conn: state, lvl = "online", "green"
        else:
            cls = m.get("class")
            if cls == "always_on":  # quiet after 10 min, offline after 30; 2 missed polls before it can go red
                if (age is not None and age <= t["seen_red_min"]) or s["missed"] < t["debounce_polls"]: state, lvl = "quiet", "yellow"
                else: state, lvl = "offline", "red"
            elif cls == "retiring": state, lvl = "offline", "yellow"  # yellow, not red, during the migration
            else:  # laptops, desktops, phones: never red
                state = "asleep" if age is not None and age <= t["quiet_hours"] * 60 else "offline"; lvl = "grey"
        pr = probe.get(m["id"]) or {}; pat = parse(pr.get("at"))
        hb = None; hb_age = None
        if m.get("heartbeat"):  # optional read-only reporter (heartbeat/); preferred over ListMachines + one-off checks
            hd = jload(D.parent / m["heartbeat"], {}); b = (hd.get("beats") or [None])[0]
            bat = parse((b or {}).get("at"))
            if bat:
                hb = b; hb_age = (now - bat).total_seconds() / 60
                if hb_age <= t["seen_red_min"]:  # quiet after 10, offline after 30: heartbeat data wins
                    state, lvl = ("online", "green") if hb_age <= t["seen_yellow_min"] else ("quiet", "yellow")
                    if hb_age <= t["seen_yellow_min"]: s["last_seen"] = iso(bat) if not seen or bat > seen else s.get("last_seen")
                    pr = {"at": b["at"], "disk_pct": (b.get("disk") or {}).get("pct_used"), "ports": b.get("ports") or {}}; pat = bat
                else: hb = None
        fresh = bool(pat and (now - pat).total_seconds() / 60 <= t["probe_fresh_min"])
        disk = pr.get("disk_pct") if isinstance(pr.get("disk_pct"), (int, float)) else None
        svcs = []
        for sv in m.get("services", []):
            if not sv.get("expected"):
                svcs.append({"name": sv["name"], "port": sv.get("port"), "state": "n/a", "level": "grey", "note": sv.get("grey_note", "Not expected here")}); continue
            v = (pr.get("ports") or {}).get(str(sv.get("port")))
            if v not in ("up", "down"): sst, sl = "unknown", "grey"
            elif not fresh: sst, sl = v, "yellow"  # last known value, but no fresh data
            elif v == "up": sst, sl = "up", "green"
            else: sst, sl = "down", (sv.get("down", "red") if conn else "yellow")
            svcs.append({"name": sv["name"], "port": sv.get("port"), "state": sst, "level": sl, "stale": bool(v in ("up", "down") and not fresh)})
        if hb is not None:  # launchd jobs reported by the heartbeat, read-only
            for j in hb.get("jobs") or []:
                nm = (m.get("job_names") or {}).get(j.get("label"), j.get("label"))
                lg = (hb.get("logs") or {}).get((m.get("job_logs") or {}).get(j.get("label"), "")) or {}
                if not j.get("loaded"): js, jl, note = "not loaded", "red", "launchd job not loaded"
                elif j.get("state") == "running": js, jl, note = "running", "green", "Running now"
                elif not j.get("runs"): js, jl, note = "waiting", "grey", "No run yet."
                elif j.get("last_exit") == 0: js, jl, note = "ok", "green", "Last run exited 0"
                else: js, jl, note = "failed", "red", "Last run exit %s" % j.get("last_exit_text")
                if lg.get("line"): note += " · log: " + lg["line"][:120]
                svcs.append({"name": nm, "port": None, "state": js, "level": jl, "note": note, "runs": j.get("runs")})
        dl = disk_level(disk, t)
        rows.append({"key": m["key"], "name": m["name"], "icon": m.get("icon", "server"), "role": m.get("role", ""), "class": m.get("class"),
            "state": state, "connected": conn, "last_seen": s.get("last_seen"), "disk_pct": disk, "disk_level": dl, "disk_as_of": iso(pat) if disk is not None else None,
            "services": svcs, "services_as_of": iso(pat) if pr.get("ports") else None, "pinned": m.get("pinned"), "notes": m.get("notes", []),
            "heartbeat": ({"at": hb.get("at"), "age_min": round(hb_age, 1), "seq": hb.get("seq"), "uptime_s": hb.get("uptime_s"), "load": hb.get("load"),
                           "power": (hb.get("power") or {}).get("source"), "free_gb": (hb.get("disk") or {}).get("free_gb")} if hb is not None else None),
            "level": worst(lvl, dl if disk is not None else None, *[x["level"] for x in svcs if x["level"] != "grey"])})
    # the box itself: free, local, read-only
    try:
        u = shutil.disk_usage("/"); bp = round(u.used * 100 / u.total)
        rows.append({"key": "box", "name": "This computer", "icon": "server", "role": "Runs machines_health.py", "class": "always_on", "state": "online", "connected": True,
            "last_seen": iso(now), "disk_pct": bp, "disk_level": disk_level(bp, t), "disk_as_of": iso(now), "services": [], "notes": [], "level": worst("green", disk_level(bp, t))})
    except Exception: pass
    static = []
    for x in cfg.get("static", []):
        r = {k: x.get(k) for k in ("key", "name", "icon", "role", "as_of", "source", "disk_pct", "updates", "addons", "notes", "state")}
        if x.get("addons") is not None:
            ls = [disk_level(x.get("disk_pct"), t) if x.get("disk_pct") is not None else None]
            for ad in x["addons"]:
                ad["level"] = "green" if ad.get("state") == "started" else ("red" if ad.get("key") else "yellow")
                ls.append(ad["level"]); ls.append("yellow" if ad.get("update") else None)
            ls.append("yellow" if x.get("updates") else None)
            r["level"] = worst(*ls); r["state"] = "snapshot"
        else: r["level"] = "yellow" if x.get("notes") else "grey"
        static.append(r)
    out = {"generated_at": iso(now), "listed_at": iso(now) if listed is not None else None, "thresholds": t, "machines": rows, "static": static,
           "heartbeat": any(r.get("heartbeat") for r in rows),
           "note": cfg.get("note") or "Machines with a heartbeat report every 5 min (read-only). Others: online state from your bot's machine list; disk and services from one-off checks."}
    pathlib.Path(a.state).write_text(json.dumps(st, indent=1))
    tmp = pathlib.Path(a.out + ".tmp"); tmp.write_text(json.dumps(out, indent=1)); tmp.replace(a.out)
    print("wrote", a.out, "·", sum(1 for r in rows if r["state"] == "online"), "of", len(rows), "online")
if __name__ == "__main__": main()
