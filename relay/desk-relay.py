#!/usr/bin/env python3
"""Desk relay: forwards Desk messages to the webhook. Listens on 127.0.0.1 only. Also stores the page layout (GET/POST /layout -> $DESK_DIR/layout.json, default ~/Desk)
and installed widget packages (GET/POST/DELETE /widgets -> $DESK_DIR/widgets/<id>/). Every request needs the header X-Desk: 1."""
import json, os, re, shutil, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
DIR = os.path.expanduser("~/.config/desk-relay"); CFG = os.path.join(DIR, "config.json")
DESK = os.path.expanduser(os.environ.get("DESK_DIR", "~/Desk")); LAYOUT = os.path.join(DESK, "layout.json")
WDIR = os.path.join(DESK, "widgets")
WID = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
WPATH = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]{0,63}(/[A-Za-z0-9_-][A-Za-z0-9._-]{0,63}){0,3}$")
WEXT = (".html", ".js", ".css", ".json", ".svg", ".txt", ".md")
WSCOPES = {"theme", "time", "storage", "network", "projects.summary", "calendar.today", "unread.counts"}
MAX_FILE, MAX_PKG, MAX_FILES = 256 * 1024, 1024 * 1024, 40
def wsafe(rel):
    if not WPATH.match(rel) or ".." in rel.split("/") or not rel.lower().endswith(WEXT): return None
    return rel
def wcheck(d):
    """Validate an install request. Returns (id, files, meta) or raises ValueError."""
    m = d.get("manifest"); files = d.get("files")
    if not isinstance(m, dict) or not isinstance(files, dict): raise ValueError("need manifest and files")
    wid = str(m.get("id", ""))
    if not WID.match(wid): raise ValueError("bad id")
    if not isinstance(m.get("entry"), str) or m["entry"] not in files: raise ValueError("entry file missing")
    if len(files) > MAX_FILES: raise ValueError("too many files")
    tot = 0
    for k, v in files.items():
        if not isinstance(k, str) or not wsafe(k) or k == "manifest.json" or k.startswith("_desk"): raise ValueError("bad file path: %r" % str(k)[:80])
        if not isinstance(v, str): raise ValueError("files must be text")
        n = len(v.encode()); tot += n
        if n > MAX_FILE: raise ValueError("file too large: " + k)
    if tot > MAX_PKG: raise ValueError("package too large")
    perms = [p for p in (m.get("permissions") or []) if p in WSCOPES]
    grants = [g for g in (d.get("grants") or []) if g in perms]
    meta = {"grants": grants, "enabled": bool(d.get("enabled", True)), "installed_at": d.get("installed_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": str(d.get("source", ""))[:500]}
    return wid, files, meta
def wread(wid):
    base = os.path.join(WDIR, wid)
    try:
        with open(os.path.join(base, "manifest.json")) as f: m = json.load(f)
        with open(os.path.join(base, "_desk.json")) as f: meta = json.load(f)
        files = {}
        for root, _, names in os.walk(base):
            for n in names:
                rel = os.path.relpath(os.path.join(root, n), base).replace(os.sep, "/")
                if rel in ("manifest.json", "_desk.json") or not wsafe(rel): continue
                with open(os.path.join(root, n), encoding="utf-8") as f: files[rel] = f.read()
        return {"manifest": m, "files": files, **meta}
    except Exception: return None
def wlist():
    if not os.path.isdir(WDIR): return []
    return [w for w in (wread(i) for i in sorted(os.listdir(WDIR)) if WID.match(i)) if w]
def wwrite(wid, m, files, meta):
    os.makedirs(WDIR, exist_ok=True)
    tmp = os.path.join(WDIR, ".tmp-" + wid); old = os.path.join(WDIR, ".old-" + wid); dst = os.path.join(WDIR, wid)
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    real = os.path.realpath(tmp)
    for rel, txt in files.items():
        fp = os.path.realpath(os.path.join(tmp, rel))
        if not fp.startswith(real + os.sep): raise ValueError("path escapes widget folder")
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f: f.write(txt)
    with open(os.path.join(tmp, "manifest.json"), "w") as f: json.dump(m, f, indent=1)
    with open(os.path.join(tmp, "_desk.json"), "w") as f: json.dump(meta, f)
    shutil.rmtree(old, ignore_errors=True)
    if os.path.isdir(dst): os.replace(dst, old)
    os.replace(tmp, dst); shutil.rmtree(old, ignore_errors=True)
PORT = int(os.environ.get("DESK_RELAY_PORT", "8765"))
def read_layout():
    try:
        with open(LAYOUT) as f: return json.load(f)
    except Exception: return None
def load():
    try:
        with open(CFG) as f: c = json.load(f)
        return c if c.get("url") and c.get("auth") else None
    except Exception: return None
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass  # never log
    def _hdr(self, code, ctype="application/json"):
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "null")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Desk")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Cache-Control", "no-store")
    def _j(self, code, obj):
        b = json.dumps(obj).encode(); self._hdr(code); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _ok_origin(self):
        o = self.headers.get("Origin")
        if o is not None and o != "null": self._j(403, {"ok": False, "error": "origin not allowed"}); return False
        if self.command != "OPTIONS" and self.headers.get("X-Desk") != "1":  # forces a CORS preflight; plain navigations/forms can't add it
            self._j(403, {"ok": False, "error": "missing X-Desk header"}); return False
        return True
    def _body(self, cap=100000):
        n = int(self.headers.get("Content-Length") or 0)
        if n > cap: raise ValueError("too large")
        return json.loads(self.rfile.read(n) or b"{}")
    def do_OPTIONS(self):
        if not self._ok_origin(): return
        self._hdr(204); self.send_header("Content-Length", "0"); self.end_headers()
    def do_GET(self):
        if not self._ok_origin(): return
        p = self.path.split("?")[0]
        if p == "/health": self._j(200, {"ok": True, "configured": load() is not None, "layout": True, "widgets": True})
        elif p == "/widgets": self._j(200, {"ok": True, "widgets": wlist()})
        elif p == "/layout": self._j(200, {"ok": True, "layout": read_layout()})
        else: self._j(404, {"ok": False, "error": "not found"})
    def do_DELETE(self):
        if not self._ok_origin(): return
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path); wid = (parse_qs(u.query).get("id") or [""])[0]
        if u.path != "/widgets" or not WID.match(wid): return self._j(400, {"ok": False, "error": "bad id"})
        dst = os.path.join(WDIR, wid)
        if not os.path.isdir(dst): return self._j(404, {"ok": False, "error": "not installed"})
        shutil.rmtree(dst); return self._j(200, {"ok": True})
    def do_POST(self):
        if not self._ok_origin(): return
        p = self.path.split("?")[0]
        try: d = self._body(int(MAX_PKG * 1.6) if p == "/widgets" else 100000)
        except Exception: return self._j(400, {"ok": False, "error": "bad json or too large"})
        if p == "/widgets":
            if isinstance(d, dict) and d.get("action") == "set":  # enable/disable or change grants without touching files
                wid = str(d.get("id", "")); w = wread(wid) if WID.match(wid) else None
                if not w: return self._j(404, {"ok": False, "error": "not installed"})
                perms = set(w["manifest"].get("permissions") or [])
                meta = {"grants": [g for g in d.get("grants", w["grants"]) if g in perms and g in WSCOPES], "enabled": bool(d.get("enabled", w["enabled"])),
                        "installed_at": w["installed_at"], "source": w.get("source", "")}
                with open(os.path.join(WDIR, wid, "_desk.json"), "w") as f: json.dump(meta, f)
                return self._j(200, {"ok": True})
            try:
                wid, files, meta = wcheck(d if isinstance(d, dict) else {})
                wwrite(wid, d["manifest"], files, meta)
            except ValueError as e: return self._j(400, {"ok": False, "error": str(e)})
            except Exception as e: return self._j(500, {"ok": False, "error": "write failed: " + type(e).__name__})
            return self._j(200, {"ok": True, "id": wid})
        if p == "/config":
            u, a = str(d.get("url", "")).strip(), str(d.get("auth", "")).strip()
            if not u.startswith("https://") or not a: return self._j(400, {"ok": False, "error": "need https url and auth"})
            os.makedirs(DIR, mode=0o700, exist_ok=True); os.chmod(DIR, 0o700)
            fd = os.open(CFG + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f: json.dump({"url": u, "auth": a}, f)
            os.replace(CFG + ".tmp", CFG); os.chmod(CFG, 0o600)
            return self._j(200, {"ok": True, "configured": True})
        if p == "/send":
            c = load()
            if not c: return self._j(503, {"ok": False, "error": "not configured"})
            if not isinstance(d, dict) or not str(d.get("message", "")).strip(): return self._j(400, {"ok": False, "error": "message required"})
            req = urllib.request.Request(c["url"], data=json.dumps(d).encode(), method="POST",
                headers={"Content-Type": "application/json", "Authorization": c["auth"]})
            try:
                with urllib.request.urlopen(req, timeout=20) as r: return self._j(200, {"ok": True, "upstream_status": r.status})
            except urllib.error.HTTPError as e: return self._j(502, {"ok": False, "upstream_status": e.code, "error": "upstream HTTP %d" % e.code})
            except Exception as e: return self._j(502, {"ok": False, "error": "upstream unreachable: " + type(e).__name__})
        if p == "/layout":  # layout only: no secrets, size capped by _body
            if not isinstance(d, dict) or d.get("version") != 1 or not isinstance(d.get("sections"), list):
                return self._j(400, {"ok": False, "error": "need layout version 1 with sections"})
            try:
                os.makedirs(DESK, exist_ok=True)
                if os.path.exists(LAYOUT): os.replace(LAYOUT, os.path.join(DESK, "layout.prev.json"))
                with open(LAYOUT + ".tmp", "w") as f: json.dump(d, f, indent=1)
                os.replace(LAYOUT + ".tmp", LAYOUT)
            except Exception as e: return self._j(500, {"ok": False, "error": "write failed: " + type(e).__name__})
            return self._j(200, {"ok": True, "saved": True})
        self._j(404, {"ok": False, "error": "not found"})
if __name__ == "__main__":
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
