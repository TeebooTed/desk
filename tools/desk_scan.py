#!/usr/bin/env python3
"""desk_scan: pre-build / pre-deploy safety scanner for Desk. Fails closed.

Blocks: secrets/tokens/private keys, email addresses not on the allowlist, dollar amounts, IPv4 addresses
(other than loopback), and cross-org leakage between your areas (optional, tools/scan_orgs.json).
Never prints a matched value: only the rule, where it was found and a masked hint (first 2 chars + length).

Library:  findings = scan_payload(name, obj, area_of=None); findings += scan_html(text)
CLI:      python3 tools/desk_scan.py index.html [more files...]   (exit 1 on any blocking finding)
Allowlist: tools/scan_allow.json {"emails": [...], "ips": [...], "phrases": [...]} - only add values that are already
           public or already shown on Desk. Org rules: tools/scan_orgs.json (see scan_orgs.example.json;
           hard = domains/servers, block; soft = names, warn only). No file = no cross-org check.
"""
import json, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent
ALLOW = json.loads((HERE / "scan_allow.json").read_text()) if (HERE / "scan_allow.json").exists() else {}
A_EMAIL = {e.lower() for e in ALLOW.get("emails", [])}
A_IP = set(ALLOW.get("ips", [])) | {"127.0.0.1", "0.0.0.0"}
A_PHRASE = [p.lower() for p in ALLOW.get("phrases", [])]

SECRET = [  # high-confidence patterns, safe to run on the whole page
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("openai-style-key", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}")),
    ("xai-key", re.compile(r"\bxai-[A-Za-z0-9]{30,}")),
    ("slack-token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("aws-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("stripe-key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("url-credentials", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/:@\"'<>]+:[^\s/@\"'<>]{3,}@")),
]
SECRET_DATA = SECRET + [  # data only (the page code legitimately says token=, Bearer, password)
    ("assigned-secret", re.compile(r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|bearer)\b\s*[:=]?\s*[\"']?(?=[A-Za-z0-9+/_.=-]{12,})(?=[^\s\"']*\d)(?=[^\s\"']*[A-Za-z])[A-Za-z0-9+/_.=-]{12,}")),
    ("hex-secret", re.compile(r"\b[0-9a-f]{48,}\b")),
]
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
MONEY = re.compile(r"(?:\$\s?\d[\d,]*(?:\.\d+)?(?:\s?[kKmMbB]\b)?|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|dollars)\b)")
IPV4 = re.compile(r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])")
# Cross-org: hard markers (domains, servers, mailboxes) fail when found in another org's area; soft names only warn.
ORGS = {k: v for k, v in (json.loads((HERE / "scan_orgs.json").read_text()) if (HERE / "scan_orgs.json").exists() else {}).items() if not k.startswith("_")}
ORG_AREAS = set(ORGS)

def _mask(v): v = str(v); return "%s…(%d chars)" % (v[:2], len(v))
def _allowed_phrase(ctx): c = ctx.lower(); return any(p in c for p in A_PHRASE)

def _walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from _walk(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from _walk(v, "%s[%d]" % (path, i))
    elif isinstance(o, str): yield path, o

def _scan_text(where, s, rules, data=True):
    out = []
    for name, rx in rules:
        for m in rx.finditer(s): out.append(("BLOCK", name, where, _mask(m.group(0))))
    if not data: return out
    for m in EMAIL.finditer(s):
        if m.group(0).lower() not in A_EMAIL: out.append(("BLOCK", "email", where, _mask(m.group(0))))
    for m in MONEY.finditer(s):
        ctx = s[max(0, m.start() - 30):m.end() + 30]
        if not _allowed_phrase(ctx): out.append(("BLOCK", "dollar-amount", where, _mask(m.group(0))))
    for m in IPV4.finditer(s):
        if m.group(0) not in A_IP: out.append(("BLOCK", "ip-address", where, _mask(m.group(0))))
    return out

def scan_payload(name, obj):
    """Scan one JSON payload that gets baked into the page."""
    out = []
    for path, s in _walk(obj): out += _scan_text("%s:%s" % (name, path), s, SECRET_DATA)
    return out

def scan_orgs(areas, extra=()):
    """areas: {area: [project dicts]}; extra: [(area, where, obj)] e.g. live.due items. Cross-org check."""
    out = []
    items = [(a, "projects:%s/%s" % (a, p.get("id") or p.get("name")), p) for a, ps in (areas or {}).items() for p in ps] + list(extra)
    for a, where, obj in items:
        if a not in ORG_AREAS: continue
        text = "\n".join(s for _, s in _walk(obj))
        for org, r in ORGS.items():
            if org == a: continue
            for m in re.finditer(r["hard"], text, re.I):
                out.append(("BLOCK", "cross-org:%s-in-%s" % (org, a), where, _mask(m.group(0))))
            for m in re.finditer(r["soft"], text, re.I):
                out.append(("WARN", "org-mention:%s-in-%s" % (org, a), where, _mask(m.group(0))))
    return out

def scan_html(text, where="index.html"):
    return _scan_text(where, text, SECRET, data=False)

def report(findings, label="desk_scan"):
    blocks = [f for f in findings if f[0] == "BLOCK"]; warns = [f for f in findings if f[0] == "WARN"]
    seen = set()
    for f in blocks + warns:
        k = f[:3]
        if k in seen: continue
        seen.add(k); print("%s %s %s at %s [%s]" % (label, f[0], f[1], f[2], f[3]))
    print("%s: %d blocking, %d warnings" % (label, len(blocks), len(warns)))
    return not blocks

if __name__ == "__main__":
    fs = []
    for p in sys.argv[1:] or ["index.html"]:
        t = pathlib.Path(p).read_text(encoding="utf-8", errors="replace")
        fs += scan_html(t, p)
        for m in re.finditer(r'<script id="desk-scan-data" type="application/json">(.*?)</script>', t, re.S):
            fs += scan_payload(p + "#data", json.loads(m.group(1).replace("<\\/", "</")))
    sys.exit(0 if report(fs) else 1)
