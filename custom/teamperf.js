/* ===== Desk team performance: per-agent KPI score vs target, 28-day sparkline, last run, open improvement,
   new recurring job status. Read-only: data comes from data/team_perf.json via build.py (LIVE.team_perf). ===== */
(function(){
const TP=(typeof LIVE!="undefined"&&LIVE&&LIVE.team_perf)||null,grid=document.getElementById("tml"),host=document.getElementById("tmv");
if(!grid||!host)return;
const E=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fdt=v=>{try{return new Date(v).toLocaleString("en-US",{month:"short",day:"numeric",hour:"numeric",minute:"2-digit"})}catch(e){return v}};
const SL={green:"On target",amber:"Below target",red:"Off target",grey:"No data yet"};
function spark(S){const W=132,H=28,n=S.length;if(!n)return"";const x=i=>(i*(W-4)/(n-1||1)+2).toFixed(1),y=v=>(H-3-(v/100)*(H-6)).toFixed(1);
 let p="",seg=[];S.forEach((s,i)=>{if(s.v==null){if(seg.length)p+=`<polyline points="${seg.join(" ")}"/>`;seg=[];return}seg.push(x(i)+","+y(s.v))});if(seg.length)p+=`<polyline points="${seg.join(" ")}"/>`;
 const dots=S.map((s,i)=>s.v==null?"":`<circle cx="${x(i)}" cy="${y(s.v)}" r="${i>=n-7?1.9:1.3}"><title>${E(s.d)}: ${s.v}</title></circle>`).join("");
 const has=S.some(s=>s.v!=null);if(!has)return'<span class="tpne">No runs logged in 28 days</span>';
 return `<svg class="tpsp" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${has?"Daily score, last 28 days":"No daily data yet"}"><rect class="tp7" x="${x(n-7)-2}" y="0" width="${W-x(n-7)+2}" height="${H}"/><line class="tpt" x1="0" x2="${W}" y1="${y(90)}" y2="${y(90)}"/>${p}${dots}</svg>`}
function fv(k,v){if(v==null)return"no data yet";return v+(k.unit=="%"?"%":k.unit?" "+k.unit:"")}
function card(a){const lim=a.limited,st=a.status,tr=a.avg7!=null&&a.prev7!=null?a.avg7-a.prev7:null;
 const imp=(a.improvements||[])[0],rt=a.routines||[];
 return `<div class="tp" data-tp="${E(a.name)}">
 <div class="tph"><i class="tpd d-${st}" aria-hidden="true"></i><span class="tps">${a.score==null?"No data yet":`Score <b>${a.score}</b><small>/100 · target 90</small>`}</span><span class="tpl lv-${st}">${lim?"Limited data":SL[st]}</span></div>
 <div class="tpr">${spark(a.series||[])}<span class="tpa">daily 7d ${a.avg7==null?"–":a.avg7}${tr==null?"":tr>0?' <em class="up">▲'+tr+"</em>":tr<0?' <em class="dn">▼'+(-tr)+"</em>":""}<br>daily 28d ${a.avg28==null?"–":a.avg28}</span></div>
 <p class="tpm">${a.coverage||"0/0"} KPIs measured · ${a.auto_kpis} auto · ${a.log_lines} log lines</p>
 <p class="tpm">Last run: ${a.last_run?E(fdt(a.last_run)):"none logged yet"}</p>
 ${imp?`<p class="tpi" title="${E(imp.what)}"><span class="tpc ${E(imp.status)}">${imp.status=="trial"?"Testing":"To improve"}</span>${E(imp.what)}</p>`:'<p class="tpm">No open improvement item.</p>'}
 ${rt.map(r=>`<p class="tpm tpj"><span class="tpc rt-${E(r.status)}">${E(r.status.replace(/_/g," "))}</span>${E(r.name)} · ${E(r.schedule)}</p>`).join("")}
 <details class="tpk"><summary>KPIs</summary><ul>${(a.kpis||[]).map(k=>`<li class="lv-${k.status}"><i class="tpd d-${k.status}" aria-hidden="true"></i><span>${E(k.label)}</span><b>${E(fv(k,k.v7))}</b><small>target ${E(k.dir)} ${E(k.target)}${k.unit=="%"?"%":k.unit?" "+E(k.unit):""} · ${k.source=="auto"?"auto":"self-logged"} · 28d ${E(fv(k,k.v28))}</small></li>`).join("")}</ul><p class="tpg">${E(a.goal)}</p></details></div>`}
function paint(){
 let sum=document.getElementById("tpsum");
 if(!TP){if(!sum){sum=document.createElement("p");sum.id="tpsum";sum.className="tpsum";host.insertBefore(sum,grid)}sum.textContent="Team performance: no data yet. Run tools/team_perf.py before build.py.";return}
 const A=TP.agents||[],by={};A.forEach(a=>by[a.name]=a);
 const LD=A.find(a=>a.lead);  /* the lead agent ("lead": true in agents.json) gets its own card if it isn't a listed teammate */
 if(LD&&![...grid.querySelectorAll(".tm")].some(c=>(c.querySelector("b")||{}).textContent===LD.name)){const h=document.createElement("div");h.className="tm tmh";h.dataset.tpn=LD.name;h.innerHTML=`<b>${E(LD.name)}</b><span class="rl">${E(LD.role)}</span><p>${E(LD.lead_note||"")}</p>`;grid.prepend(h)}
 grid.querySelectorAll(".tm").forEach(c=>{const n=(c.querySelector("b")||{}).textContent,a=by[n];if(!a||c.querySelector(".tp"))return;c.dataset.tpn=n;c.classList.add("tp-"+a.status);c.insertAdjacentHTML("beforeend",`<span class="tpq" title="Performance: ${E(a.limited?"limited data":SL[a.status])}">${a.score==null||a.status=="grey"?"–":a.score}</span>`+card(a));
  c.tabIndex=0;c.setAttribute("aria-label",n+": "+(a.score==null?"no data yet":"score "+a.score)+", "+SL[a.status]+". Open performance details");
  const open=()=>{const sec=host.closest(".sec");if(!sec||!/^(s|m)$/.test(sec.dataset.size||""))return;let pop=document.getElementById("tppop");
   if(pop&&pop.dataset.for===n){pop.remove();return}if(!pop){pop=document.createElement("div");pop.id="tppop";pop.className="tppop";host.appendChild(pop)}
   pop.dataset.for=n;pop.innerHTML=`<div class="tpph"><b>${E(n)}</b><span class="rl">${E(a.role)}</span><button type="button" class="tpx" aria-label="Close">×</button></div>`+card(a);
   pop.querySelector(".tpx").onclick=()=>pop.remove()};
  c.addEventListener("click",open);c.addEventListener("keydown",e=>{if(e.key=="Enter"||e.key==" "){e.preventDefault();open()}})});
 const cnt={green:0,amber:0,red:0,grey:0};A.forEach(a=>cnt[a.status]++);
 if(!sum){sum=document.createElement("div");sum.id="tpsum";sum.className="tpsum";host.insertBefore(sum,grid)}
 sum.innerHTML=`<span class="tpsh" title="Left dot on each teammate = performance; right dot = desk-log activity">Performance</span>${["green","amber","red","grey"].map(s=>`<span class="tpcn"><i class="tpd d-${s}" aria-hidden="true"></i>${cnt[s]} ${SL[s].toLowerCase()}</span>`).join("")}<span class="tpsr">Self-reviews ${E(TP.review&&TP.review.self_review||"")}. Team review ${E((TP.review&&TP.review.team_review||"").replace(/^Mondays/,"Mondays"))}. Data as of ${E(fdt(TP.generated))}.${TP.demo?" Example data (examples/team-perf).":""}</span>`;
 sum.title=TP.method||"";
 const ts=document.getElementById("tms");if(ts&&!ts.dataset.tp){ts.dataset.tp=1;ts.textContent+=` · ${cnt.green} on target · ${cnt.amber+cnt.red} below`}}
window.TPERF={paint};paint();
})();
