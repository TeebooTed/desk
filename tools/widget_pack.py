#!/usr/bin/env python3
"""Package a Desk widget folder.
  python3 tools/widget_pack.py path/to/widget
Writes sha256 for every file into manifest.json, builds <id>-<version>.zip next to the folder,
and prints the manifest's sha256 (use it to pin the widget in registry.json or the URL installer)."""
import hashlib, json, pathlib, sys, zipfile
d = pathlib.Path(sys.argv[1]).resolve(); mp = d / "manifest.json"
m = json.loads(mp.read_text())
files = sorted(p for p in d.rglob("*") if p.is_file() and p.name != "manifest.json" and not any(x.startswith(".") for x in p.relative_to(d).parts))
m["sha256"] = {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
mp.write_text(json.dumps(m, indent=2) + "\n")
z = d.parent / f"{m['id']}-{m['version']}.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(mp, "manifest.json")
    for p in files: zf.write(p, p.relative_to(d).as_posix())
print("zip:", z); print("manifest sha256:", hashlib.sha256(mp.read_bytes()).hexdigest())
