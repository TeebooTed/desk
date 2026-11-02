const $ = id => document.getElementById(id);
const CODES = {0:"Clear",1:"Mostly clear",2:"Partly cloudy",3:"Cloudy",45:"Fog",48:"Fog",51:"Drizzle",53:"Drizzle",55:"Drizzle",56:"Freezing drizzle",57:"Freezing drizzle",61:"Rain",63:"Rain",65:"Heavy rain",66:"Freezing rain",67:"Freezing rain",71:"Snow",73:"Snow",75:"Heavy snow",77:"Snow grains",80:"Showers",81:"Showers",82:"Heavy showers",85:"Snow showers",86:"Snow showers",95:"Thunderstorm",96:"Thunderstorm",99:"Thunderstorm"};
function icon(c, day) {
  if (c == 0) return day ? "\u2600\ufe0f" : "\ud83c\udf19";
  if (c == 1) return day ? "\ud83c\udf24\ufe0f" : "\ud83c\udf19";
  if (c == 2) return day ? "\u26c5" : "\u2601\ufe0f";
  if (c == 3) return "\u2601\ufe0f";
  if (c == 45 || c == 48) return "\ud83c\udf2b\ufe0f";
  if (c >= 51 && c <= 57) return "\ud83c\udf26\ufe0f";
  if ((c >= 61 && c <= 67) || (c >= 80 && c <= 82)) return "\ud83c\udf27\ufe0f";
  if ((c >= 71 && c <= 77) || c == 85 || c == 86) return "\ud83c\udf28\ufe0f";
  if (c >= 95) return "\u26c8\ufe0f";
  return "";
}
let loc = { lat: 33.45, lon: -112.07 }; // Phoenix
async function load() {
  try {
    const u = `https://api.open-meteo.com/v1/forecast?latitude=${loc.lat}&longitude=${loc.lon}&current=temperature_2m,weather_code,is_day&daily=temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&timezone=auto&forecast_days=1`;
    const j = await (await fetch(u)).json();
    const ic = icon(j.current.weather_code, Number(j.current.is_day) === 1);
    $("ic").textContent = ic; $("ic").title = CODES[j.current.weather_code] || "";
    $("big").textContent = Math.round(j.current.temperature_2m) + "°";
    $("sub").textContent = `${CODES[j.current.weather_code] || ""} · H ${Math.round(j.daily.temperature_2m_max[0])}° L ${Math.round(j.daily.temperature_2m_min[0])}°`;
  } catch (e) { $("ic").textContent = ""; $("big").textContent = "—"; $("sub").textContent = "Couldn't reach Open-Meteo"; }
}
const theme = x => x && document.documentElement.style.setProperty("--fg", x.fg || (x.mode == "dark" ? "#eee" : "#111"));
desk.on("theme", theme);
desk.on("refresh", load);
desk.ready().then(async r => {
  theme(r.theme);
  try { const s = await desk.storage.get("loc"); if (s && s.set === true && isFinite(+s.lat) && isFinite(+s.lon)) loc = { lat: +s.lat, lon: +s.lon }; /* only a location the user saved; otherwise Phoenix */ } catch (e) {}
  $("lat").value = loc.lat; $("lon").value = loc.lon; load();
});
$("go").onclick = async () => {
  const lat = +$("lat").value, lon = +$("lon").value;
  if (!(Math.abs(lat) <= 90 && Math.abs(lon) <= 180)) return;
  loc = { lat, lon }; await desk.storage.set("loc", { lat, lon, set: true }); load();
};
