#!/usr/bin/env python3
"""Regenerate Desk index.html from status.json. Usage: python3 build.py [status.json]"""
import json, sys, pathlib, datetime, zoneinfo
here = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else str(here / "example-status.json"))
data = json.loads(src.read_text()) if src.exists() else {"areas": {}, "generated": "not set up yet"}  # empty -> first-run setup card
data.setdefault("areas", {})
# Areas (any number of columns). Optional keys in status.json:
#   "area_order":  ["Work", "Side", "Personal"]      column order; defaults to the order of "areas"
#   "area_labels": {"Side": "Side project"}          display names; defaults to the key
#   "area_rules":  {"Side": "regex"}                 move projects whose name matches into that area
import re as _re
for tgt, rx in (data.get("area_rules") or {}).items():
    for a in list(data["areas"]):
        if a == tgt: continue
        hit = [p for p in data["areas"][a] if _re.search(rx, p.get("name", ""), _re.I)]
        if hit:
            data["areas"][a] = [p for p in data["areas"][a] if p not in hit]
            data["areas"].setdefault(tgt, []).extend(hit)
_order = data.get("area_order") or list(data["areas"])
data["areas"] = {**{k: data["areas"].get(k, []) for k in _order}, **{k: v for k, v in data["areas"].items() if k not in _order}}
data["area_order"] = list(data["areas"])
data["area_labels"] = {k: k for k in data["areas"]} | (data.get("area_labels") or {})
if src.name == "example-status.json":  # demo: shift example dates so the stamps read as recent
    _a = datetime.date.fromisoformat(str(data.get("generated", "2026-01-15"))[:10]); _s = datetime.date.today() - _a
    data = json.loads(_re.sub(r"(?<![\d-])(\d{4}-\d{2}-\d{2})(?![\d-])", lambda m: (datetime.date.fromisoformat(m.group(1)) + _s).isoformat(), json.dumps(data)))
# Project ids and "last updated" stamps. Each project gets a stable "id" (kept if present, else a slug of its name).
# last_update may be an ISO date-time ("2026-10-23T14:44:00-07:00") or a bare date; optional "updated_by" names who did it.
_TZ = zoneinfo.ZoneInfo(data["tz"]) if data.get("tz") else datetime.datetime.now().astimezone().tzinfo
_ZN = {"PT": "America/Los_Angeles", "MT": "America/Denver", "CT": "America/Chicago", "ET": "America/New_York", "UTC": "UTC"}
def _slug(n): return _re.sub(r"[^a-z0-9]+", "-", str(n).lower()).strip("-")[:48] or "project"
_seen = set()
for ps in data["areas"].values():
    for p in ps:
        if p.get("id"): _seen.add(str(p["id"]))
for ps in data["areas"].values():
    for p in ps:
        if not p.get("id"):
            b = _slug(p.get("name", "")); i = b; n = 2
            while i in _seen: i = "%s-%d" % (b, n); n += 1
            p["id"] = i; _seen.add(i)
# Agent progress log (agentlog): updates.jsonl next to build.py (or $DESK_UPDATES), one JSON object per line, written by ./desk-log.
# status.json stays the base. For each project the newest log entry newer than its last_update sets last_update/updated_by,
# and the newest such entries carrying percent/status/next_step set those. Notes go to the top of "recent" (deduped,
# newest first). priority (and any other field) is never touched. kind:new_project entries are proposals for your bot to review.
import os as _os
_UPD = pathlib.Path(_os.environ.get("DESK_UPDATES", here / "updates.jsonl"))
_LOGST = {"active": "active", "blocked": "blocked", "on_hold": "on hold", "on hold": "on hold", "hold": "on hold", "done": "done"}
def _when(s, end=False):
    s = str(s or "").strip()
    try:
        if _re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return datetime.datetime.fromisoformat(s + (" 23:59:59" if end else " 00:00:00")).replace(tzinfo=_TZ)
        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=_TZ)
    except Exception: return None
_log = {}; _props = []
if _UPD.exists():
    for _n, _l in enumerate(_UPD.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not _l.strip(): continue
        try:
            e = json.loads(_l); w = _when(e.get("at"))
            if not isinstance(e, dict) or w is None or not e.get("agent"): raise ValueError("missing at/agent")
        except Exception as ex:
            print("updates.jsonl line %d skipped: %s" % (_n, ex)); continue
        e["_w"] = w
        if e.get("kind") == "new_project": _props.append(e); continue
        if e.get("project_id") and e.get("note"): _log.setdefault(str(e["project_id"]), []).append(e)
_known = {p["id"]: p for ps in data["areas"].values() for p in ps}
for _pid in [k for k in _log if k not in _known]: print("updates.jsonl: unknown project id %r ignored" % _pid)
for _pid, es in _log.items():
    p = _known.get(_pid)
    if not p: continue
    es.sort(key=lambda e: e["_w"])
    base = _when(p.get("last_update"), end=False)
    new = [e for e in es if base is None or e["_w"] >= base]
    if new:
        top = new[-1]
        p["last_update"] = top["_w"].isoformat(); p["updated_by"] = str(top["agent"])[:40]
        for k in ("percent", "status", "next_step"):
            v = next((e[k] for e in reversed(new) if e.get(k) not in (None, "")), None)
            if v is None: continue
            if k == "percent":
                try: v = max(0, min(100, int(v)))
                except Exception: continue
            if k == "status":
                v = _LOGST.get(str(v).strip().lower())
                if not v: continue
            p[k] = v
    notes = ["%s: %s (%s)" % (e["_w"].astimezone(_TZ).strftime("%Y-%m-%d %H:%M %Z"), " ".join(str(e["note"]).split()), e["agent"]) for e in reversed(es)]
    seen, rec = set(), []
    for r in notes + list(p.get("recent") or []):
        key = _re.sub(r"\W+", " ", str(r).lower()).strip()
        if key in seen: continue
        seen.add(key); rec.append(r)
    p["recent"] = rec[:12]
data["proposed_projects"] = [{"name": e.get("name"), "area": e.get("area"), "agent": e.get("agent"), "at": e["_w"].isoformat(), "note": e.get("note", "")} for e in _props]
def _upd(p):
    """_upd = {at: ISO with offset, date_only}. A bare date takes the latest timed 'recent' entry on that day
    ("YYYY-MM-DD HH:MM", optional PT/MT/CT/ET/UTC); otherwise end of that day, so date-only cards are never flagged early."""
    lu = str(p.get("last_update") or "").strip()
    if not lu: return None
    try:
        if not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", lu):
            d = datetime.datetime.fromisoformat(lu.replace("Z", "+00:00"))
            if d.tzinfo is None: d = d.replace(tzinfo=_TZ)
            return {"at": d.isoformat(), "date_only": False}
        best = None
        for r in p.get("recent") or []:
            m = _re.match(r"(\d{4}-\d{2}-\d{2})\s+~?(\d{1,2}):(\d{2})\s*(PT|MT|CT|ET|UTC)?\b", str(r))
            if not m or m.group(1) != lu: continue
            z = zoneinfo.ZoneInfo(_ZN[m.group(4)]) if m.group(4) else _TZ
            d = datetime.datetime.fromisoformat("%s %02d:%s" % (m.group(1), int(m.group(2)), m.group(3))).replace(tzinfo=z)
            best = d if best is None or d > best else best
        if best: return {"at": best.isoformat(), "date_only": False}
        d = datetime.datetime.fromisoformat(lu + " 23:59:59").replace(tzinfo=_TZ)
        return {"at": d.isoformat(), "date_only": True}
    except Exception as e:
        print("bad last_update", p.get("name"), lu, e); return None
for ps in data["areas"].values():
    for p in ps:
        u = _upd(p)
        if u: p["_upd"] = u
        else: p.pop("_upd", None)
import re, difflib
flag = []
for md in src.parent.glob("*.md"):
    for line in md.read_text().splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 3 and "UNVERIFIED" in c[2]:
            flag.append(c[0].lower())
for ps in data["areas"].values():
    for p in ps:
        n = p["name"].lower()
        if any(difflib.SequenceMatcher(None, n, f).ratio() > 0.6 or n in f for f in flag):
            p["unverified"] = True
now = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%b %-d, %Y %-I:%M %p %Z")
import os
lv = pathlib.Path(os.environ.get("DESK_LIVE", here / "live.json"))
if not lv.exists() and len(sys.argv) <= 1: lv = here / "example-live.json"  # demo mode
live = json.loads(lv.read_text()) if lv.exists() else {}
wd = here / "tiles"  # plugin widgets: one JSON object (or list) per file, merged after live["widgets"]
if wd.is_dir():
    for f in sorted(wd.glob("*.json")):
        try:
            w = json.loads(f.read_text()); live.setdefault("widgets", []).extend(w if isinstance(w, list) else [w])
        except Exception as e: print("skip widget", f.name, e)
if lv.name == "example-live.json":  # demo: shift example dates so "today" is always today
    import re as _re
    anchor = datetime.date.fromisoformat(live.get("fetched", "2026-10-23")[:10])
    shift = datetime.date.today() - anchor
    def _mv(m): return (datetime.date.fromisoformat(m.group(1)) + shift).isoformat()
    live = json.loads(_re.sub(r"(\d{4}-\d{2}-\d{2})(?=T|\")", _mv, json.dumps(live)))
# ---- Desk features (org filter, "as of" stamps, machines, routine history, teammate badges, stale guard) ----
# Org filter tooltips: optional "org_tips" {"Work": "Day-job projects only."} in status.json. Areas not listed still show.
data["org_tips"] = data.get("org_tips") or {}
# Due items follow the same area_rules as projects, so the org filter can place them.
for _d in live.get("due") or []:
    if not isinstance(_d, dict): continue
    for _tg, _rx in (data.get("area_rules") or {}).items():
        if _d.get("area") != _tg and _re.search(_rx, str(_d.get("title", "")), _re.I): _d["area"] = _tg; break
# Optional calendar -> area map for Today: "cal_org": {"Work calendar": "Work"} in status.json.
data["cal_org"] = data.get("cal_org") or {}
# "As of" stamps: when each input last changed. The page shows these per panel and in the header pill.
def _mt(f):
    try: return datetime.datetime.fromtimestamp(pathlib.Path(f).stat().st_mtime, _TZ).replace(microsecond=0).isoformat()
    except Exception: return None
_demo = src.name == "example-status.json"
data["asof"] = {"status": _mt(src), "updates": _mt(_UPD), "live": _mt(lv), "built": datetime.datetime.now(_TZ).replace(microsecond=0).isoformat()}
# Machines panel: data/machines_health.json, written by tools/machines_health.py ($DESK_MACHINES overrides).
# Demo mode uses examples/machines/machines_health.example.json with its times moved up to now.
_mh = pathlib.Path(os.environ.get("DESK_MACHINES", here / "data" / "machines_health.json"))
if not _mh.exists() and _demo: _mh = here / "examples" / "machines" / "machines_health.example.json"
try: machines = json.loads(_mh.read_text()) if _mh.exists() else None
except Exception as e: print("machines_health.json skipped:", e); machines = None
if machines and _mh.name.endswith(".example.json"):
    _g = datetime.datetime.fromisoformat(machines["generated_at"]); _sh = datetime.datetime.now(_g.tzinfo) - _g
    def _mvt(m): return (datetime.datetime.fromisoformat(m.group(0)) + _sh).replace(microsecond=0).isoformat()
    machines = json.loads(_re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", _mvt, json.dumps(machines)))
_now = datetime.datetime.now(_TZ)
def _iso(ts): return datetime.datetime.fromtimestamp(ts, _TZ).isoformat(timespec="seconds")
# Refresh routine run history (read-only). If your refresh routine backs up status.json as
# status.pre-refresh-<slot>.json before each run (and live.json as live.pre-refresh-<slot>.json when it rewrites it),
# Desk lists the last runs. Backups are looked for next to status.json ($DESK_REFRESH_BACKUPS overrides).
_bk = pathlib.Path(os.environ.get("DESK_REFRESH_BACKUPS", src.parent))
_runs = []
for _f in sorted(_bk.glob("status.pre-refresh-*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:14]:
    _slot = _f.stem.split("pre-refresh-")[-1]
    _runs.append({"slot": _slot, "at": _iso(_f.stat().st_mtime), "status_json": True, "live_json": (here / ("live.pre-refresh-%s.json" % _slot)).exists() or (_bk / ("live.pre-refresh-%s.json" % _slot)).exists()})
if not _runs and _demo:  # demo: twice-daily runs, one of which skipped the live panels
    _runs = [{"slot": "demo%d" % i, "at": (_now - datetime.timedelta(hours=12 * i + 2)).isoformat(timespec="seconds"), "status_json": True, "live_json": i != 2} for i in range(6)]
if _runs:
    live["routine_history"] = {"name": data.get("refresh_routine_name") or "Desk progress refresh", "runs": _runs,
        "source": "backup files written by each run (status.pre-refresh-*, live.pre-refresh-*)"}
# Teammate activity recency from the desk log (updates.jsonl): newest entry per agent.
_ta = {}
if _UPD.exists():
    for _ln in _UPD.read_text(encoding="utf-8", errors="replace").splitlines():
        try: _u = json.loads(_ln)
        except Exception: continue
        _ag, _at = _u.get("agent"), _u.get("at")
        if isinstance(_ag, str) and isinstance(_at, str) and _at > _ta.get(_ag, ""): _ta[_ag] = _at
live["team_activity"] = _ta
# Stale-live guard: warn (and write LIVE_STALE) when live.json is older than "live_stale_hours" (default 13).
if not _demo and live:
    try: _lage_h = (_now - datetime.datetime.fromisoformat(live.get("fetched"))).total_seconds() / 3600
    except Exception: _lage_h = None
    _stale_flag = here / "LIVE_STALE"
    if _lage_h is None or _lage_h > float(data.get("live_stale_hours", 13)):
        print("WARNING: live.json fetched is %s old. Your refresh routine should rewrite live.json each run." % ("unknown" if _lage_h is None else "%.1fh" % _lage_h))
        _stale_flag.write_text("live.json fetched=%s age_h=%s checked=%s\n" % (live.get("fetched"), None if _lage_h is None else round(_lage_h, 1), _now.isoformat(timespec="seconds")))
    elif _stale_flag.exists(): _stale_flag.unlink()
# Team performance: data/team_perf.json from tools/team_perf.py (run it before build.py; $DESK_TEAMPERF overrides).
# Demo mode with no data file: built on the fly from examples/team-perf/. Missing -> the panel says "no data yet".
_tpf = pathlib.Path(os.environ.get("DESK_TEAMPERF", here / "data" / "team_perf.json"))
live["team_perf"] = None
try:
    if _tpf.exists(): live["team_perf"] = json.loads(_tpf.read_text())
    elif _demo and "DESK_TEAMPERF" not in os.environ:
        sys.path.insert(0, str(here / "tools")); import team_perf as _tpm
        live["team_perf"] = _tpm.collect(here / "examples" / "team-perf")[0]
except Exception as e: print("team_perf skipped:", e); live["team_perf"] = None
if live["team_perf"]:
    try:
        _tpa = (_now - datetime.datetime.fromisoformat(live["team_perf"]["generated"])).total_seconds() / 3600
        if _tpa > 13: print("WARNING: team_perf.json is %.1fh old; run tools/team_perf.py before build.py." % _tpa)
    except Exception: pass
t = (here / "template.html").read_text()
import layout_lib
lay, lay_def = layout_lib.load(here, os.environ.get("DESK_LAYOUT"))
t = t.replace("__LAYOUT_JSON__", json.dumps(lay).replace("</", "<\\/")).replace("__LAYOUT_DEFAULT_JSON__", json.dumps(lay_def).replace("</", "<\\/"))
t = t.replace("/*__LIVE__*/null", json.dumps(live).replace("</", "<\\/"))
t = t.replace("/*__DATA__*/null", json.dumps(data).replace("</", "<\\/")).replace("/*__BUILT__*/", now)
wid_dir = os.environ.get("DESK_WIDGETS", str(here / "widgets"))
reg, bundled = layout_lib.load_registry(here)
t = t.replace("/*__WIDGETS__*/null", layout_lib.js_json(layout_lib.load_widgets(wid_dir))).replace("/*__REGISTRY__*/null", layout_lib.js_json(reg)).replace("/*__BUNDLED__*/null", layout_lib.js_json(bundled))
# Feature assets: custom/features.css + custom/features.js (org filter, stamps, machines, palette) and
# custom/alerts.css + custom/alerts.js (alerts, run history, teammate badges), plus icons/*.svg.
_ic = {}
for _f in sorted((here / "icons").glob("*.svg")):
    try:
        _sv = _f.read_text(encoding="utf-8").strip()
        if not _sv.startswith("<svg") or _re.search(r"<script|\bon\w+\s*=|javascript:|<foreignObject|href\s*=", _sv, _re.I): raise ValueError("unsafe svg")
        _ic[_f.stem] = _re.sub(r'\s(width|height)="[^"]*"', "", _sv, count=2)
    except Exception as e: print("icon", _f.name, "skipped:", e)
for _ph, _fn in (("/*__B1CSS__*/", "features.css"), ("/*__B1JS__*/", "features.js"), ("/*__B2CSS__*/", "alerts.css"), ("/*__B2JS__*/", "alerts.js")):
    _tx = (here / "custom" / _fn).read_text(encoding="utf-8")
    if "</style" in _tx or "</script" in _tx: sys.exit("custom/%s contains a closing tag" % _fn)
    t = t.replace(_ph, _tx, 1)
t = t.replace("/*__B1ART__*/null", json.dumps(_ic).replace("</", "<\\/")).replace("/*__MACHINES__*/null", json.dumps(machines).replace("</", "<\\/"))
# Team performance panel (custom/teamperf.*) and themes (custom/theme.*: palettes, picker; runs in <head> before first paint).
for _ph, _fn in (("/*__TPCSS__*/", "teamperf.css"), ("/*__TPJS__*/", "teamperf.js"), ("/*__THCSS__*/", "theme.css"), ("/*__THJS__*/", "theme.js")):
    _tx = (here / "custom" / _fn).read_text(encoding="utf-8")
    if "</style" in _tx or "</script" in _tx: sys.exit("custom/%s contains a closing tag" % _fn)
    t = t.replace(_ph, _tx, 1)
# Safety scan: fail closed. Nothing is written if anything blocks. See tools/desk_scan.py and docs/safety-scan.md.
sys.path.insert(0, str(here / "tools")); import desk_scan
_fs = desk_scan.scan_payload("status", data) + desk_scan.scan_payload("live", live) + desk_scan.scan_payload("layout", lay) + desk_scan.scan_payload("machines", machines or {})
_fs += desk_scan.scan_orgs(data["areas"], [(d.get("area"), "live:due/%s" % d.get("title", "")[:40], d) for d in live.get("due") or [] if isinstance(d, dict)])
_fs += desk_scan.scan_html(t, "page")
if not desk_scan.report(_fs, "scan"):
    print("BUILD STOPPED: safety scan failed; index.html not written."); sys.exit(2)
out = pathlib.Path(os.environ.get("DESK_OUT", here / "index.html"))
out.write_text(t)
print("wrote", out)
