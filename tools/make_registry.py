#!/usr/bin/env python3
"""Rebuild registry.json from examples/widgets/* (and keep extra third-party entries already listed)."""
import hashlib, json, pathlib
here = pathlib.Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/TeebooTed/desk/main/"
regp = here / "registry.json"
old = json.loads(regp.read_text()) if regp.exists() else {"version": 1, "widgets": []}
keep = [w for w in old.get("widgets", []) if not w.get("bundled")]
out = []
for d in sorted((here / "examples" / "widgets").iterdir()):
    mp = d / "manifest.json"
    if not mp.exists(): continue
    m = json.loads(mp.read_text()); rel = d.relative_to(here).as_posix()
    out.append({"id": m["id"], "name": m["name"], "author": m.get("author", ""), "description": m.get("description", ""), "version": m["version"],
                "permissions": m.get("permissions", []), "manifest": RAW + rel + "/manifest.json", "sha256": hashlib.sha256(mp.read_bytes()).hexdigest(), "bundled": rel})
regp.write_text(json.dumps({"version": 1, "widgets": out + keep}, indent=2) + "\n"); print("registry:", len(out + keep), "widgets")
