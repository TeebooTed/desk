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
t = (here / "template.html").read_text()
import layout_lib
lay, lay_def = layout_lib.load(here, os.environ.get("DESK_LAYOUT"))
t = t.replace("__LAYOUT_JSON__", json.dumps(lay).replace("</", "<\\/")).replace("__LAYOUT_DEFAULT_JSON__", json.dumps(lay_def).replace("</", "<\\/"))
t = t.replace("/*__LIVE__*/null", json.dumps(live).replace("</", "<\\/"))
t = t.replace("/*__DATA__*/null", json.dumps(data).replace("</", "<\\/")).replace("/*__BUILT__*/", now)
wid_dir = os.environ.get("DESK_WIDGETS", str(here / "widgets"))
reg, bundled = layout_lib.load_registry(here)
t = t.replace("/*__WIDGETS__*/null", layout_lib.js_json(layout_lib.load_widgets(wid_dir))).replace("/*__REGISTRY__*/null", layout_lib.js_json(reg)).replace("/*__BUNDLED__*/null", layout_lib.js_json(bundled))
out = pathlib.Path(os.environ.get("DESK_OUT", here / "index.html"))
out.write_text(t)
print("wrote", out)
