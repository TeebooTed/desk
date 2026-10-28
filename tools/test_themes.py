#!/usr/bin/env python3
"""Theme tests: WCAG AA contrast for every preset palette (light + dark) and for derived Custom palettes,
pre-paint application, persistence, legacy-accent migration, the Appearance picker and a hardcoded-colour sweep.
Uses example data only: copies the repo to a temp folder and builds the demo there. Screenshots of every preset
go to that temp folder (or $DESK_SHOTS). Needs: pip install playwright && playwright install chromium.
Run: python3 tools/test_themes.py"""
import asyncio, json, os, pathlib, re, shutil, subprocess, sys, tempfile
from playwright.async_api import async_playwright
HERE = pathlib.Path(__file__).resolve().parent.parent
T = pathlib.Path(tempfile.mkdtemp()) / "desk"
TOP = {".git", "live.json", "status.json", "data", "index.html", "team-perf"}  # your own data stays out; examples/ comes along
shutil.copytree(HERE, T, ignore=lambda d, names: [n for n in names if (pathlib.Path(d) == HERE and n in TOP) or n == "__pycache__"])
D = str(T); OUT = os.environ.get("DESK_SHOTS", str(T / "shots")) + "/"; os.makedirs(OUT, exist_ok=True)
subprocess.run([sys.executable, str(T / "build.py")], cwd=T, env=dict(os.environ, DESK_OUT=str(T / "index.html")), check=True)
src = open(D + "/custom/theme.js").read()
PAL = json.loads(re.search(r"/\*PAL_BEGIN\*/(.*?)/\*PAL_END\*/", src, re.S).group(1))
def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def cr(a, b):
    x, y = sorted([lum(a), lum(b)]); return (y + 0.05) / (x + 0.05)
CHECKS = [("fg", "bg", 4.5), ("fg", "bg2", 4.5), ("fg", "card", 4.5), ("fg2", "card", 4.5), ("fg2", "bg", 4.5), ("mut", "card", 4.5), ("mut", "bg", 4.5), ("mut", "bg2", 4.5),
          ("acc", "card", 4.5), ("acc", "bg", 4.5), ("acc", "acc-s", 4.5), ("on-acc", "acc", 4.5)] + \
         [("p-%s" % s, "p-%s-bg" % s, 4.5) for s in ("active", "done", "blocked", "hold")] + [("p-%s" % s, "card", 4.5) for s in ("done", "blocked", "hold")] + \
         [("c-%s" % s, k, 3.0) for s in ("active", "done", "blocked", "hold") for k in ("card", "bg")] + [("card", "c-blocked", 4.5 if False else 3.0)]
def check(name, p, fails, rows):
    worst = {}
    for a, b, t in CHECKS:
        r = cr(p[a], p[b]); worst[a + "/" + b] = round(r, 2)
        if r < t: fails.append("%s %s/%s %.2f < %s" % (name, a, b, r, t))
    rows[name] = {"fg/card": worst["fg/card"], "fg/bg": worst["fg/bg"], "mut(min)": min(worst["mut/card"], worst["mut/bg"], worst["mut/bg2"]),
                  "acc text(min)": min(worst["acc/card"], worst["acc/bg"], worst["acc/acc-s"]), "on-acc": worst["on-acc/acc"],
                  "pill text(min)": min(v for k, v in worst.items() if k.startswith("p-")), "status dot(min)": min(v for k, v in worst.items() if k.startswith("c-"))}
CUSTOM = {"bg": "#1d1b2e", "card": "#2a2740", "bd": "#433d66", "acc": "#ffb347", "fg": ""}
async def main():
    fails, rows, errs, res = [], {}, [], {}
    for pid, modes in PAL.items():
        for m, p in modes.items(): check("%s/%s" % (pid, m), p, fails, rows)
    assert set(PAL) >= {"spring", "summer", "fall", "winter", "hacker"}, "missing preset"
    # hardcoded-colour sweep: every hex in custom CSS must be overridden or be org identity / icon art
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        async def page(init, scheme="light"):
            ctx = await b.new_context(viewport={"width": 1440, "height": 1000}, color_scheme=scheme)
            pg = await ctx.new_page()
            await pg.route("http://127.0.0.1*/**", lambda r: r.abort())
            await pg.add_init_script("""(()=>{%s
              new MutationObserver((ms,o)=>{if(document.body&&!window.__firstBg){window.__firstBg=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();window.__firstPal=document.documentElement.dataset.pal;o.disconnect()}}).observe(document,{childList:true,subtree:true})})()""" % init)
            pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
            pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "net::ERR" not in m.text and "Failed to load resource" not in m.text else None)
            await pg.goto("file://" + D + "/index.html"); await pg.wait_for_timeout(900); return ctx, pg
        async def popshot(pg, path):
            bb = await pg.evaluate("(()=>{const e=document.getElementById('thm');const p=e.closest('[role=dialog],.pop,dialog,[popover]')||e.parentElement;p.scrollIntoView({block:'nearest'});const r=p.getBoundingClientRect();return {x:Math.max(0,r.x-8),y:Math.max(0,r.y-8),width:Math.min(1440,r.width+16),height:Math.min(1000,r.height+16)}})()")
            await pg.screenshot(path=path, clip=bb)
        once = "if(!sessionStorage.getItem('t')){sessionStorage.setItem('t',1);%s}"
        # 1) each preset (light; seasonal also dark) + screenshot
        for pid in ["spring", "summer", "fall", "winter", "hacker", "classic"]:
            for scheme in (["light", "dark"] if pid in ("spring", "summer", "fall", "winter") else ["light"]):
                ctx, pg = await page(once % ("localStorage.setItem('desk-pal',JSON.stringify({id:'%s'}))" % pid), scheme)
                st = await pg.evaluate("""()=>{const cs=getComputedStyle(document.documentElement),R=document.documentElement;return {pal:R.dataset.pal,theme:R.dataset.theme||'',bg:cs.getPropertyValue('--bg').trim(),acc:cs.getPropertyValue('--acc').trim(),
                  first:window.__firstBg,font:getComputedStyle(document.body).fontFamily,tt:getComputedStyle(document.getElementById('tt')).display,bodyBg:getComputedStyle(document.body).backgroundColor}}""")
                exp = PAL[pid]["dark" if (scheme == "dark" or pid == "hacker") else "light"]
                key = "%s/%s" % (pid, scheme)
                res[key] = st
                if st["pal"] != pid or st["bg"] != exp["bg"] or st["acc"] != exp["acc"]: fails.append("%s applied wrong: %s" % (key, st))
                if st["first"] != exp["bg"]: fails.append("%s not applied before first paint (first --bg %s)" % (key, st["first"]))
                if pid == "hacker" and (st["theme"] != "dark" or "mono" not in st["font"].lower() or st["tt"] != "none"): fails.append("hacker fixed-dark/mono failed %s" % st)
                if pid == "hacker":  # sweep: no element may still paint a legacy hardcoded status/accent colour
                    sw = await pg.evaluate("""()=>{const bad=['rgb(47, 111, 237)','rgb(192, 57, 43)','rgb(46, 158, 91)','rgb(201, 162, 39)','rgb(154, 160, 166)','rgb(46, 125, 79)','rgb(154, 122, 18)'],o=[];
                      for(const e of document.querySelectorAll('body *')){if(e.closest('.orgc,[data-o]'))continue;for(const pse of [null,'::before']){const cs=getComputedStyle(e,pse);for(const p of ['color','backgroundColor','borderTopColor','stroke','fill']){const v=cs[p];if(bad.some(b=>v.includes(b.slice(4,-1))))o.push((e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className)+(pse||'')+' '+p+' '+v)}}}
                      return {left:[...new Set(o)].slice(0,20),team:document.querySelectorAll('.tm').length}}""")
                    res["hardcoded_sweep_hacker"] = sw
                    if sw["left"]: fails.append("hardcoded colours remain: %s" % sw["left"])
                if pid in ("spring", "summer", "fall", "winter", "hacker") and (scheme == "light" or pid != "hacker"):
                    await pg.screenshot(path=OUT + "%s%s.png" % (pid, "" if scheme == "light" else "-dark"))
                await ctx.close()
        # 2) legacy accent migration (no desk-pal, saved layout has appearance.accent)
        ctx, pg = await page(once % "localStorage.setItem('desk-layout',JSON.stringify({version:1,updated:'2099-01-01T00:00:00Z',sections:[],appearance:{accent:'#c2185b'}}))")
        m = await pg.evaluate("()=>({pal:document.documentElement.dataset.pal,acc:getComputedStyle(document.documentElement).getPropertyValue('--acc').trim(),saved:localStorage.getItem('desk-pal'),first:window.__firstPal,t:window.__deskTheme.get()})")
        res["migration"] = m
        if m["pal"] != "custom" or m["acc"] != "#c2185b" or m["first"] != "custom": fails.append("migration failed %s" % m)
        await ctx.close()
        # 3) picker: open Appearance, choose Custom, live preview, persist, reset, then reload
        ctx, pg = await page(once % "localStorage.setItem('desk-pal',JSON.stringify({id:'winter'}))")
        await pg.click("#edt"); await pg.wait_for_timeout(200); await pg.click("#ea"); await pg.wait_for_timeout(250)
        res["picker_buttons"] = await pg.locator("#thm [data-thp]").all_inner_texts()
        if await pg.locator("#lypop [data-acc]").count(): fails.append("old accent control still present")
        await popshot(pg, OUT + "picker-winter.png")
        await pg.click("#thm [data-thp=custom]"); await pg.wait_for_timeout(150)
        for k, v in CUSTOM.items():
            if v: await pg.eval_on_selector("#thm [data-thc=%s]" % k, "(e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))}", v)
        live = await pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()")
        if live != CUSTOM["bg"]: fails.append("live preview failed %s" % live)
        await pg.eval_on_selector("#thm [data-thc=acc]", "e=>e.dispatchEvent(new Event('change',{bubbles:true}))"); await pg.wait_for_timeout(150)
        cp = await pg.evaluate("window.__deskTheme.get()")
        res["custom"] = {"state": cp["custom"], "theme": await pg.evaluate("document.documentElement.dataset.theme"), "report": await pg.inner_text("#thm .thcr")}
        check("custom(sample)", cp["palette"], fails, rows)
        await popshot(pg, OUT + "custom-picker.png")
        await pg.click("#thm .lpx") if await pg.locator("#thm .lpx").count() else await pg.keyboard.press("Escape")
        await pg.keyboard.press("Escape"); await pg.click("#edt") if await pg.locator("#ebar:not([hidden])").count() else None
        await pg.reload(); await pg.wait_for_timeout(900)
        rl = await pg.evaluate("({pal:document.documentElement.dataset.pal,bg:getComputedStyle(document.documentElement).getPropertyValue('--bg').trim(),first:window.__firstBg,ls:localStorage.getItem('desk-pal')})")
        res["custom_reload"] = rl
        if rl["pal"] != "custom" or rl["bg"] != CUSTOM["bg"] or rl["first"] != CUSTOM["bg"]: fails.append("custom not persisted %s" % rl)
        await pg.screenshot(path=OUT + "custom.png")
        # reset to preset
        await pg.click("#edt"); await pg.wait_for_timeout(200); await pg.click("#ea"); await pg.wait_for_timeout(200)
        await pg.select_option("#thm [data-thbase]", "fall"); await pg.click("#thm [data-threset]"); await pg.wait_for_timeout(150)
        rs = await pg.evaluate("window.__deskTheme.get().custom")
        if rs["bg"] != PAL["fall"]["light"]["bg"] or rs["acc"] != PAL["fall"]["light"]["acc"]: fails.append("reset failed %s" % rs)
        await pg.click("#thm [data-thp=spring]"); await pg.wait_for_timeout(100)
        if await pg.evaluate("document.documentElement.dataset.pal") != "spring": fails.append("switch back failed")
        await ctx.close()
        # 4) derived Custom palettes stay AA for a spread of user colours
        ctx, pg = await page("")
        for i, c in enumerate([{"bg": "#ffffff", "card": "#fafafa", "acc": "#ffcc00"}, {"bg": "#000000", "card": "#111111", "acc": "#0000ff"}, {"bg": "#7f7f7f", "card": "#808080", "acc": "#808080"},
                               {"bg": "#ffe4f0", "card": "#fff7fb", "acc": "#ff69b4"}, {"bg": "#002b36", "card": "#073642", "acc": "#268bd2"}]):
            p = await pg.evaluate("c=>window.__deskTheme.derive(c)", c)
            # only the derived (auto) colours are guaranteed; accent itself is the user's pick
            sub = []; check("derived%d" % i, p, sub, {})
            fails += [f for f in sub if not re.search(r"/(acc|on-acc)|acc/|acc-s", f)]
        await ctx.close(); await b.close()
    res["errors"] = errs
    print(json.dumps({"contrast": rows, "results": res}, indent=1))
    if errs: fails += errs
    print("FAILS:", fails if fails else "none"); sys.exit(1 if fails else 0)
asyncio.run(main())
