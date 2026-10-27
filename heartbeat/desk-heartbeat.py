#!/usr/bin/python3
"""Desk heartbeat: optional, read-only status reporter for one Mac (example; adapt for your machines).
Writes ~/Desk/heartbeat.json every run (launchd com.example.desk-heartbeat, StartInterval 300).
Collects: time, uptime, disk, load, power, local port up/down, launchd job status, last result line of a log you name.
Settings: config.json next to this file (see config.example.json). Copy heartbeat.json to Desk's data/ folder
(e.g. with your bot or a sync tool) and point "heartbeat" at it in data/machines_config.json.
Never reads env vars, secrets, or process command lines. No network except connect() to 127.0.0.1 ports."""
import json, os, re, shutil, socket, subprocess, time, datetime
HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HOME, "Desk", "heartbeat.json")
KEEP = 12

def cfg():
    try: return json.load(open(os.path.join(HERE, "config.json")))
    except Exception: return {}

def run(args):
    try: return subprocess.run(args, capture_output=True, text=True, timeout=10).stdout
    except Exception: return ""

def port_up(p):
    s = socket.socket(); s.settimeout(1)
    try: s.connect(("127.0.0.1", int(p))); return True
    except Exception: return False
    finally: s.close()

def uptime_s():
    m = re.search(r"sec = (\d+)", run(["/usr/sbin/sysctl", "-n", "kern.boottime"]))
    return int(time.time()) - int(m.group(1)) if m else None

def power():
    t = run(["/usr/bin/pmset", "-g", "batt"])
    src = re.search(r"'([^']+)'", t); pct = re.search(r"(\d+)%", t)
    return {"source": src.group(1) if src else None, "battery_pct": int(pct.group(1)) if pct else None}

def job(label):
    t = run(["/bin/launchctl", "print", "gui/%d/%s" % (os.getuid(), label)])
    if not t: return {"label": label, "loaded": False}
    g = lambda k: (re.search(r"^\s*%s = (.+)$" % re.escape(k), t, re.M) or [None, None])[1]
    runs = g("runs"); code = g("last exit code")
    return {"label": label, "loaded": True, "state": g("state"),
            "runs": int(runs) if runs and runs.isdigit() else None,
            "last_exit": int(code) if code and re.fullmatch(r"-?\d+", code) else None,
            "last_exit_text": code}

SCRUB = [(re.compile(r"[A-Za-z0-9_\-]{24,}"), "[redacted]"), (re.compile(r"\S+@\S+"), "[email]"),
         (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b"), "[ip]"), (re.compile(r"(?i)(token|key|secret|pass\w*|auth)\S*"), "[redacted]")]

def log_tail(path, n=200):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2); f.seek(max(0, f.tell() - 16384)); lines = f.read().decode("utf-8", "replace").splitlines()
    except Exception: return {"exists": os.path.exists(path), "line": None, "mtime": None}
    pick = next((l for l in reversed(lines) if re.search(r"(?i)\b(ok|done|success|complete|finished|fail|error|rows|synced)\b", l)), None)
    pick = pick or next((l for l in reversed(lines) if l.strip()), None)
    if pick:
        for rx, rep in SCRUB: pick = rx.sub(rep, pick)
        pick = pick.strip()[:n]
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat(timespec="seconds")
    return {"exists": True, "line": pick, "mtime": mt}

def disk(path):
    # Same numbers as `df -k` (APFS: shutil's "used" counts the whole container, so read df's own columns).
    try:
        out = subprocess.run(["/bin/df", "-k", path], capture_output=True, text=True, timeout=10).stdout.splitlines()[-1].split()
        used, avail = int(out[2]), int(out[3])
        return {"pct_used": -(-used * 100 // (used + avail)), "free_gb": round(avail * 1024 / 1e9, 1)}
    except Exception:
        du = shutil.disk_usage(path)
        return {"pct_used": round(du.used * 100 / du.total), "free_gb": round(du.free / 1e9, 1)}

def main():
    c = cfg()
    beat = {"at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "uptime_s": uptime_s(),
            "disk": disk(c.get("disk_path", "/System/Volumes/Data")),
            "load": [round(x, 2) for x in os.getloadavg()],
            "power": power(),
            "ports": {str(p): ("up" if port_up(p) else "down") for p in c.get("ports", [8765])},
            "jobs": [job(l) for l in c.get("jobs", [])],
            "logs": {k: log_tail(os.path.expanduser(v)) for k, v in c.get("logs", {}).items()}}
    try: prev = json.load(open(OUT)).get("beats", [])
    except Exception: prev = []
    seq = (prev[0].get("seq", 0) if prev else 0) + 1; beat["seq"] = seq
    doc = {"_note": "Desk heartbeat, read-only.", "device": c.get("device", "my-mac"),
           "interval_s": 300, "beats": ([beat] + prev)[:KEEP]}
    tmp = OUT + ".tmp"; json.dump(doc, open(tmp, "w"), indent=1); os.replace(tmp, OUT)

if __name__ == "__main__": main()
