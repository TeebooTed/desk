#!/usr/bin/env python3
"""Browser tests for the Desk features (org filter, palette, alerts + snooze, run history, teammate badges,
approval cards, machines/heartbeat). Uses example data only: copies the repo to a temp folder, tags a few
example Waiting items with areas, adds one approval in "Work", builds the demo, and drives it with Playwright.
Needs: pip install playwright && playwright install chromium.  Run: python3 tools/test_features.py"""
import asyncio, json, os, pathlib, shutil, subprocess, sys, tempfile
from playwright.async_api import async_playwright
HERE = pathlib.Path(__file__).resolve().parent.parent
T = pathlib.Path(tempfile.mkdtemp()) / "desk"
shutil.copytree(HERE, T, ignore=shutil.ignore_patterns(".git", "live.json", "status.json", "data", "index.html"))
lv = json.loads((T / "example-live.json").read_text())
lv["waiting"] = [dict(w, area="Work") for w in lv.get("waiting", [])] + [
    {"id": "t-ap1", "kind": "post", "to": "Work account", "q": "Test post for the approval card", "preview": "Example text.", "area": "Work"},
    {"id": "t-w1", "q": "Test question for Side", "area": "Side", "opts": ["Yes", "No"]}]
(T / "example-live.json").write_text(json.dumps(lv))
FX = str(T / "index.html")
subprocess.run([sys.executable, str(T / "build.py")], cwd=T, env=dict(os.environ, DESK_OUT=FX), check=True)
async def main():
    r, errs, sent, dialogs = {}, [], [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 1000}); pg = await ctx.new_page()
        async def rt(x):
            if x.request.url.endswith("/send") and x.request.method == "POST":
                sent.append(json.loads(x.request.post_data)); await x.fulfill(status=200, body="{}")
            else: await x.abort()
        await pg.route("http://127.0.0.1*/**", rt)
        await pg.add_init_script("localStorage.setItem('desk-hook', JSON.stringify({url:'https://example.invalid/',configured:true}))")
        pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        pg.on("dialog", lambda d: (dialogs.append(d.message), asyncio.ensure_future(d.accept())))
        await pg.goto("file://" + FX); await pg.wait_for_timeout(1200)
        r["chips"] = await pg.locator("#orgf .orgc").all_inner_texts()
        await pg.click('#orgf .orgc[data-o="Side"]'); await pg.wait_for_timeout(200)
        r["areas_side"] = await pg.eval_on_selector_all("#areas .area", "a=>a.filter(x=>x.offsetParent).map(x=>x.dataset.area)")
        r["waiting_side"] = await pg.inner_text("#waiting")
        await pg.click('#orgf .orgc[data-o="Work"]'); await pg.wait_for_timeout(200)
        r["approval_visible"] = await pg.locator('.wi.ap[data-w="t-ap1"]').count()
        await pg.locator('.wi.ap[data-w="t-ap1"] [data-ap="Decline"]').click(); await pg.wait_for_timeout(400)
        r["sent"] = sent[:]
        await pg.click('#orgf .orgc[data-o="all"]'); await pg.wait_for_timeout(150)
        await pg.keyboard.press("Control+k"); await pg.wait_for_timeout(200)
        r["palette_open"] = await pg.is_visible(".kpo")
        await pg.keyboard.type("work"); await pg.wait_for_timeout(150)
        r["palette_hits"] = len(await pg.locator("#kpl [role=option]").all_inner_texts())
        await pg.keyboard.press("Escape")
        n0 = await pg.locator("#b2al li").count(); r["alerts"] = n0
        if n0:
            await pg.locator("#b2al li").first.locator("[data-sn='4']").click(); await pg.wait_for_timeout(200)
            r["after_snooze"] = await pg.locator("#b2al li").count()
        await pg.evaluate("document.getElementById('rtn').open=true"); await pg.wait_for_timeout(150)
        r["history"] = await pg.locator("#b2rh li").count()
        r["badges"] = await pg.locator("#tml .b2tb").count()
        r["machines"] = await pg.locator("#machines .mcard").count()
        r["heartbeat_line"] = await pg.locator("#machines .mhb").count()
        await b.close()
    print(json.dumps(r, indent=1)); print("ERRORS:", errs)
    checks = {
        "org chips": len(r["chips"]) >= 3,
        "Side filter shows only Side": r["areas_side"] == ["Side"] and "Test question for Side" in r["waiting_side"] and "launch blog" not in r["waiting_side"],
        "approval card shown": r["approval_visible"] == 1,
        "approval sends a message only": bool(r["sent"]) and r["sent"][0].get("message") == "[Desk approval] t-ap1 Decline" and r["sent"][0].get("area") == "approval",
        "palette": r["palette_open"] and r["palette_hits"] > 0,
        "alerts + snooze": r["alerts"] > 0 and r.get("after_snooze") == r["alerts"] - 1,
        "run history": r["history"] > 0, "teammate badges": r["badges"] > 0,
        "machines + heartbeat": r["machines"] >= 3 and r["heartbeat_line"] >= 1}
    bad = [k for k, v in checks.items() if not v]
    print("FAILED:" if bad else "ALL PASSED", bad or "")
    shutil.rmtree(T.parent, ignore_errors=True)
    sys.exit(1 if errs or bad else 0)
asyncio.run(main())
