#!/usr/bin/env python3
"""Regenerate Desk index.html from status.json. Usage: python3 build.py [status.json]"""
import json, sys, pathlib, datetime, zoneinfo
here = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else str(here / "example-status.json"))
data = json.loads(src.read_text()) if src.exists() else {"areas": {}, "generated": "not set up yet"}  # empty -> first-run setup card
data.setdefault("areas", {})
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
