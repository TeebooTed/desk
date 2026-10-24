"""Validate/clamp a Desk layout.json (mirrors vL() in template.html)."""
import json, re, copy, pathlib
IDS = ["setup", "today", "waiting", "ask", "tiles", "widgets", "frame", "podsta", "projects", "teammates", "activity", "routsum", "routines"]
SIZES = ["s", "m", "l", "full"]
def clamp(v, lo, hi, d):
    try: return max(lo, min(hi, int(v)))
    except Exception: return d
WSEC = re.compile(r"w:[a-z0-9][a-z0-9-]{1,40}")
WID = re.compile(r"[a-z0-9][a-z0-9-]{1,40}")
WPATH = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]{0,63}(/[A-Za-z0-9_-][A-Za-z0-9._-]{0,63}){0,3}")
WEXT = (".html", ".js", ".css", ".json", ".svg", ".txt", ".md")
def _pkg_files(base):
    files = {}; tot = 0
    for f in sorted(base.rglob("*")):
        rel = f.relative_to(base).as_posix()
        if not f.is_file() or rel in ("manifest.json", "_desk.json") or not WPATH.fullmatch(rel) or ".." in rel.split("/") or not rel.lower().endswith(WEXT): continue
        if f.stat().st_size > 256 * 1024: raise ValueError("file too large: " + rel)
        files[rel] = f.read_text(encoding="utf-8"); tot += len(files[rel].encode())
    if tot > 1024 * 1024 or len(files) > 40: raise ValueError("package too large")
    return files
def load_widgets(wdir):
    """Installed widget packages ($DESK_DIR/widgets/<id>/) to embed at build time."""
    out = []; wdir = pathlib.Path(wdir)
    if not wdir.is_dir(): return out
    for d in sorted(wdir.iterdir()):
        if not d.is_dir() or not WID.fullmatch(d.name): continue
        try:
            m = json.loads((d / "manifest.json").read_text())
            meta = json.loads((d / "_desk.json").read_text()) if (d / "_desk.json").exists() else {"grants": [], "enabled": True}
            if m.get("id") != d.name: continue
            out.append({"manifest": m, "files": _pkg_files(d), "grants": meta.get("grants", []), "enabled": meta.get("enabled", True), "installed_at": meta.get("installed_at", ""), "source": meta.get("source", "")})
        except Exception as e: print("skipping widget", d.name, "-", e)
    return out
def load_registry(here):
    """Gallery: registry.json plus any 'bundled' packages it points at (so the gallery works offline)."""
    p = here / "registry.json"
    if not p.exists(): return None, None
    reg = json.loads(p.read_text()); bundled = {}
    for r in reg.get("widgets", []):
        b = r.get("bundled")
        if not b or not WID.fullmatch(str(r.get("id", ""))): continue
        d = (here / b).resolve()
        if here.resolve() not in d.parents or not (d / "manifest.json").exists(): continue
        bundled[r["id"]] = {"manifest": (d / "manifest.json").read_text(), "files": _pkg_files(d)}
    return reg, bundled
def js_json(o):
    return json.dumps(o).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
OLDDEF = "setup:full,today:m,waiting:m,ask:full,tiles:full,widgets:full,projects:full,teammates:full,activity:full,routines:full"
def validate(lay, default):
    d = copy.deepcopy(default)
    if not isinstance(lay, dict) or lay.get("version") != 1: return d
    dsec = {s["id"]: s for s in d["sections"]}; out = []; seen = set()
    secs = [s for s in (lay.get("sections") or []) if isinstance(s, dict) and isinstance(s.get("id"), str)]
    base = [s for s in secs if not WSEC.fullmatch(s["id"])]
    if base and all(s.get("visible", True) is not False for s in base) and ",".join(f'{s["id"]}:{s.get("size")}' for s in base) == OLDDEF:
        old = {s["id"]: s for s in base}
        lay = {**lay, "sections": [{**ds, **{k: v for k, v in old.get(ds["id"], {}).items() if k not in ("id", "size", "visible")}} for ds in d["sections"]] + [s for s in secs if WSEC.fullmatch(s["id"])]}
    for s in lay.get("sections") or []:
        if isinstance(s, dict) and isinstance(s.get("id"), str) and WSEC.fullmatch(s["id"]) and s["id"] not in seen:
            seen.add(s["id"]); out.append({"id": s["id"], "visible": s.get("visible") is not False, "size": s.get("size") if s.get("size") in SIZES else "s"}); continue
        if not isinstance(s, dict) or s.get("id") not in dsec or s["id"] in seen: continue
        seen.add(s["id"]); n = {**dsec[s["id"]], **s}
        n["visible"] = bool(n.get("visible", True)); n["size"] = n["size"] if n.get("size") in SIZES else dsec[s["id"]]["size"]
        if n["id"] == "today": n["days"] = clamp(n.get("days"), 1, 3, 2)
        if n["id"] == "routines" and n.get("show") not in ("all", "failed"): n["show"] = "all"
        if n["id"] == "projects" and n.get("sort") not in ("priority", "name", "progress", "status"): n["sort"] = "priority"
        out.append(n)
    out += [copy.deepcopy(dsec[i]) for i in IDS if i not in seen]
    a = {**d["appearance"], **(lay.get("appearance") or {})}
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(a.get("accent") or "")): a["accent"] = ""
    if a.get("density") not in ("compact", "cozy", "roomy"): a["density"] = "cozy"
    a["font_scale"] = clamp(a.get("font_scale"), 90, 125, 100); a["radius"] = clamp(a.get("radius"), 0, 24, 14); a["columns"] = clamp(a.get("columns"), 0, 5, 0)
    ph = lay.get("phone") or {}; po = [i for i in ph.get("order") or [] if i in IDS or WSEC.fullmatch(str(i))]
    th = lay.get("theme") if lay.get("theme") in ("auto", "light", "dark") else "auto"
    return {"version": 1, "updated": str(lay.get("updated") or d["updated"]), "updated_by": str(lay.get("updated_by") or ""), "sections": out, "phone": {"order": po}, "appearance": a, "theme": th}
def load(here, env_path=None):
    default = json.loads((here / "layout.default.json").read_text())
    p = pathlib.Path(env_path) if env_path else here / "layout.json"
    try: lay = json.loads(p.read_text())
    except Exception: lay = default
    return validate(lay, default), default
