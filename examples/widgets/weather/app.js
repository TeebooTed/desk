const $ = id => document.getElementById(id);
const CODES = {0:"Clear",1:"Mostly clear",2:"Partly cloudy",3:"Cloudy",45:"Fog",48:"Fog",51:"Drizzle",53:"Drizzle",55:"Drizzle",61:"Rain",63:"Rain",65:"Heavy rain",71:"Snow",73:"Snow",75:"Heavy snow",80:"Showers",81:"Showers",82:"Heavy showers",95:"Thunderstorm",96:"Thunderstorm",99:"Thunderstorm"};
let loc = { lat: 40.71, lon: -74.01 };
async function load() {
  try {
    const u = `https://api.open-meteo.com/v1/forecast?latitude=${loc.lat}&longitude=${loc.lon}&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&timezone=auto&forecast_days=1`;
    const j = await (await fetch(u)).json();
    $("big").textContent = Math.round(j.current.temperature_2m) + "°";
    $("sub").textContent = `${CODES[j.current.weather_code] || ""} · H ${Math.round(j.daily.temperature_2m_max[0])}° L ${Math.round(j.daily.temperature_2m_min[0])}°`;
  } catch (e) { $("big").textContent = "—"; $("sub").textContent = "Couldn't reach Open-Meteo"; }
}
const theme = x => x && document.documentElement.style.setProperty("--fg", x.fg || (x.mode == "dark" ? "#eee" : "#111"));
desk.on("theme", theme);
desk.on("refresh", load);
desk.ready().then(async r => {
  theme(r.theme);
  try { loc = (await desk.storage.get("loc")) || loc; } catch (e) {}
  $("lat").value = loc.lat; $("lon").value = loc.lon; load();
});
$("go").onclick = async () => {
  const lat = +$("lat").value, lon = +$("lon").value;
  if (!(Math.abs(lat) <= 90 && Math.abs(lon) <= 180)) return;
  loc = { lat, lon }; await desk.storage.set("loc", loc); load();
};
