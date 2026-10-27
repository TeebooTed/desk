#!/bin/sh
# Positive test: a planted fake token, outside email, dollar amount and cross-org domain must stop the build.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d); cp -r "$HERE/." "$T/" 2>/dev/null || true
cp "$HERE/tools/scan_orgs.example.json" "$T/tools/scan_orgs.json"
python3 - "$T" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]+"/example-status.json"))
k=next(iter(d["areas"]))
fake="ghp_"+"A"*36
d["areas"][k][0]["next_step"]=f"token {fake} mail someone@example.com pay $1,250"
d["areas"]["Side"][0]["summary"]="note work.example.com"
json.dump(d,open(sys.argv[1]+"/status.test.json","w"))
PY
cd "$T"; rm -f index.html
if DESK_OUT="$T/index.html" python3 build.py status.test.json; then echo "FAIL: build passed with planted secrets"; exit 1; fi
[ ! -f index.html ] && echo "PASS: build stopped and wrote nothing"
rm -rf "$T"
