#!/usr/bin/env python3
"""Team performance panel tests on example data (examples/team-perf/): copies the repo to a temp folder and builds
(1) the demo, (2) a fixture (Ops forced red, a declined routine), (3) a no-data build and (4) Teammates at full size.
Checks a card for every agent (incl. the lead's own card), status dots, sparklines, KPI lists, the popover at small and
medium sizes, routine chips, the empty state, and no page errors, in light and dark. Also checks tools/team_perf.py
scoring on the example data and team-perf/log-run. Screenshots go to the temp folder (or $DESK_SHOTS).
Needs: pip install playwright && playwright install chromium.  Run: python3 tools/test_teamperf.py"""
import asyncio, json, os, pathlib, shutil, subprocess, sys, tempfile
from playwright.async_api import async_playwright
HERE = pathlib.Path(__file__).resolve().parent.parent
T = pathlib.Path(tempfile.mkdtemp()) / "desk"
TOP = {".git", "live.json", "status.json", "data", "index.html", "team-perf"}  # your own data stays out; examples/ comes along
shutil.copytree(HERE, T, ignore=lambda d, names: [n for n in names if (pathlib.Path(d) == HERE and n in TOP) or n == "__pycache__"])
shutil.copytree(HERE / "team-perf", T / "team-perf", ignore=lambda d, names: [n for n in names if pathlib.Path(d) == HERE / "team-perf" and n not in ("RULE_GENERAL.md", "log-run", "incident")])
D = str(T); OUT = os.environ.get("DESK_SHOTS", D + "/shots") + "/"; os.makedirs(OUT, exist_ok=True)
fails = []
# --- collector on the example data
sys.path.insert(0, D + "/tools"); import team_perf
tp = team_perf.collect(T / "examples" / "team-perf")[0]
by = {a["name"]: a for a in tp["agents"]}
exp = {"Assistant": "green", "Researcher": "green", "Writer": "red", "Designer": "grey", "Ops": "green"}
for n, s in exp.items():
    if by.get(n, {}).get("status") != s: fails.append(f"collector {n}: {by.get(n, {}).get('status')} != {s}")
if not by["Assistant"].get("lead") or sum(1 for a in tp["agents"] if a.get("lead")) != 1: fails.append("exactly one lead expected")
if not by["Designer"].get("limited"): fails.append("Designer should be limited data")
# --- log-run writes one line to $TEAM_PERF_DIR/log/<agent>.jsonl
lr = pathlib.Path(tempfile.mkdtemp())
subprocess.run([D + "/team-perf/log-run", "Writer", "newsletter", "ok", "--min", "20", "--kpi", "minutes=20", "--kpi", "approved_first=true"],
               env=dict(os.environ, TEAM_PERF_DIR=str(lr)), check=True, capture_output=True)
ln = [json.loads(x) for x in (lr / "log" / "writer.jsonl").read_text().splitlines()] if (lr / "log" / "writer.jsonl").exists() else \
     [json.loads(x) for f in (lr / "log").glob("*.jsonl") for x in f.read_text().splitlines()]
if len(ln) != 1 or ln[0].get("outcome") != "ok" or ln[0].get("kpi", {}).get("minutes") != 20: fails.append(f"log-run line {ln}")
# --- builds
fx = json.loads(json.dumps(tp))
for a in fx["agents"]:
    if a["name"] == "Ops": a.update(status="red", score=55, limited=False)
    if a["name"] == "Designer": a["routines"] = [dict(a["routines"][0], status="declined")]
FXJ = D + "/tp-fixture.json"; json.dump(fx, open(FXJ, "w"))
REAL, FX, NO, FULL = (D + "/" + x for x in ("index.html", "fixture.html", "nodata.html", "full.html"))
LAY = D + "/layout-full.json"
lay = json.load(open(D + "/layout.default.json")); tm = [x for x in lay["sections"] if x["id"] == "teammates"][0]; tm["size"] = "full"
lay["sections"] = [tm] + [x for x in lay["sections"] if x["id"] != "teammates"]; json.dump(lay, open(LAY, "w"))
for out, src, ly in ((REAL, None, None), (FX, FXJ, None), (NO, "/nonexistent/team_perf.json", None), (FULL, None, LAY)):
    e = dict(os.environ, DESK_OUT=out); e.pop("DESK_TEAMPERF", None); e.pop("DESK_LAYOUT", None)
    if src: e["DESK_TEAMPERF"] = src
    if ly: e["DESK_LAYOUT"] = ly
    subprocess.run([sys.executable, D + "/build.py"], cwd=D, env=e, check=True, capture_output=True)
NK = len(by["Researcher"]["kpis"])
async def main():
    res = {}; errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for theme in ("light", "dark"):
            for which, path in (("demo", REAL), ("fixture", FX), ("nodata", NO), ("full", FULL)):
                ctx = await b.new_context(viewport={"width": 1440, "height": 1000}, color_scheme=theme)
                pg = await ctx.new_page(); await pg.route("http://127.0.0.1*/**", lambda r: r.abort())
                pg.on("pageerror", lambda e, t=theme, w=which: errs.append(f"{t}/{w}: {e}"))
                await pg.goto("file://" + path); await pg.wait_for_timeout(1200)
                await pg.evaluate("document.getElementById('tmv').open=true"); await pg.wait_for_timeout(150)
                r = {"cards": await pg.locator("#tml .tm .tp").count(), "lead": await pg.locator('#tml .tm[data-tpn="Assistant"]').count(),
                     "sum": await pg.locator("#tpsum").inner_text(), "spark": await pg.locator("#tml .tpsp, #tml .tpne").count(),
                     "status": await pg.evaluate("[...document.querySelectorAll('#tml .tm[data-tpn]')].map(c=>c.dataset.tpn+':'+[...c.classList].find(x=>x.startsWith('tp-')))")}
                if which == "nodata":
                    if r["cards"] or "no data yet" not in r["sum"]: fails.append(f"{theme}/nodata empty state: {r}")
                else:
                    if r["cards"] != len(tp["agents"]) or r["lead"] != 1 or r["spark"] != len(tp["agents"]): fails.append(f"{theme}/{which} cards: {r}")
                    r["size"] = await pg.evaluate("document.querySelector('[data-sec=teammates]').dataset.size")
                    await pg.locator('#tml .tm[data-tpn="Researcher"]').click(); await pg.wait_for_timeout(150)
                    if r["size"] in ("s", "m"):
                        r["pop"] = await pg.locator("#tppop").count()
                        if r["pop"] != 1: fails.append(f"{theme}/{which} popover missing")
                        await pg.locator('#tppop .tpk summary').click(); await pg.wait_for_timeout(100)
                        r["kpis"] = await pg.locator('#tppop .tpk li').all_inner_texts()
                        await (await pg.query_selector("#tmv")).screenshot(path=OUT + f"teammates-{which}-{theme}-detail.png")
                        await pg.locator("#tppop .tpx").click(); await pg.wait_for_timeout(100)
                        r["pop_closed"] = await pg.locator("#tppop").count() == 0
                        if not r["pop_closed"]: fails.append(f"{theme}/{which} popover did not close")
                    else:
                        await pg.locator('#tml .tm[data-tpn="Researcher"] .tpk summary').click(); await pg.wait_for_timeout(100)
                        r["kpis"] = await pg.locator('#tml .tm[data-tpn="Researcher"] .tpk li').all_inner_texts()
                    if len(r["kpis"]) != NK: fails.append(f"{theme}/{which} Researcher KPIs {r['kpis']}")
                    if which == "demo" and "Example data" not in await pg.evaluate("document.getElementById('tpsum').textContent"): fails.append("demo should say Example data")
                if which == "demo":
                    for n, s in exp.items():
                        if f"{n}:tp-{s}" not in r["status"]: fails.append(f"{theme}/demo {n} not {s}: {r['status']}")
                if which == "fixture":
                    if "Ops:tp-red" not in r["status"]: fails.append("fixture red not applied")
                    r["chips"] = [c.lower() for c in await pg.locator("#tml .tpc").all_inner_texts()]
                    if "created" not in r["chips"] or "declined" not in r["chips"]: fails.append(f"routine chips {r['chips']}")
                if which in ("full", "nodata", "demo"): await (await pg.query_selector("#tmv")).screenshot(path=OUT + f"teammates-{which}-{theme}.png")
                res[f"{theme}/{which}"] = r; await ctx.close()
        await b.close()
    print(json.dumps(res, indent=1)[:4000]); print("errors:", errs); print("FAILS:", fails if fails else "none")
    sys.exit(1 if errs or fails else 0)
asyncio.run(main())
