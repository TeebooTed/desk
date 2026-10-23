const $ = id => document.getElementById(id);
let tz, target = null;
function paint() {
  const n = new Date(), o = tz ? { timeZone: tz } : {};
  $("t").textContent = n.toLocaleTimeString([], { ...o, hour: "numeric", minute: "2-digit" });
  $("d").textContent = n.toLocaleDateString([], { ...o, weekday: "long", month: "long", day: "numeric" });
  if (target && target.when) {
    const days = Math.ceil((new Date(target.when + "T00:00:00") - n) / 864e5);
    $("cd").textContent = days > 0 ? `${days} day${days == 1 ? "" : "s"} until ${target.label || target.when}` : days == 0 ? `${target.label || "It"} is today!` : "";
  }
}
function theme(t) { if (!t) return; document.documentElement.style.setProperty("--fg", t.fg || (t.mode == "dark" ? "#eee" : "#111")); if (t.accent) document.documentElement.style.setProperty("--acc", t.accent); }
desk.on("theme", theme);
desk.ready().then(async r => {
  theme(r.theme);
  try { tz = (await desk.getData("time")).tz; } catch (e) {}
  try { target = await desk.storage.get("target"); } catch (e) {}
  if (target) { $("lab").value = target.label || ""; $("when").value = target.when || ""; }
  paint(); setInterval(paint, 10000);
});
$("save").onclick = async () => { target = { label: $("lab").value.trim(), when: $("when").value }; await desk.storage.set("target", target); paint(); };
