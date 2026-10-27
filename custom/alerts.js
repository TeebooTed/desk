/* ===== Desk alerts: alerts banner + toast (device-local snooze), refresh run history (read-only),
   teammate activity badges. Vanilla JS, ideas only (see NOTICE). Approval cards and org-filtered Today/Waiting/counts live in template.html. ===== */
(function(){
const B2CFG={live:[13*60,26*60],team:[24,72],snoozeH:4};
const $2=s=>document.querySelector(s),SK="desk-b2-snooze",TK="desk-b2-toasted";
const okd=v=>v&&!isNaN(new Date(v));
const minsAgo=v=>okd(v)?(Date.now()-new Date(v))/6e4:null;
const agoT=v=>{const m=minsAgo(v);if(m==null)return"never";if(m<1)return"just now";if(m<60)return Math.round(m)+" min ago";const h=m/60;if(h<48)return Math.round(h)+" hr ago";return Math.round(h/24)+" days ago"};
const fmt=v=>{try{return new Date(v).toLocaleString("en-US",{timeZone:TZ,month:"short",day:"numeric",hour:"numeric",minute:"2-digit"})}catch(e){return v}};
function ld(k,d){try{return JSON.parse(localStorage.getItem(k)||"null")||d}catch(e){return d}}
function sv(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}

/* ---------- alerts ---------- */
function alerts(){const out=[],M=(typeof MACH!="undefined"&&MACH&&MACH.machines)||[],th=(MACH&&MACH.thresholds)||{disk_yellow:80,disk_red:90};
 M.forEach(m=>{
  if(m.disk_pct!=null&&m.disk_pct>=th.disk_yellow){const r=m.disk_pct>=th.disk_red;out.push({id:`disk:${m.key}:${r?"r":"y"}`,lv:r?"red":"yellow",t:`${m.name} disk ${m.disk_pct}% used`,go:"#mc-"+m.key})}
  if(m.class=="always_on"&&(m.state=="quiet"||m.state=="offline"))out.push({id:`state:${m.key}:${m.state}`,lv:m.state=="offline"?"red":"yellow",t:`${m.name} is ${m.state}${m.last_seen?` (last check-in ${agoT(m.last_seen)})`:""}`,go:"#mc-"+m.key});
  (m.services||[]).filter(s=>s.level=="red").forEach(s=>out.push({id:`svc:${m.key}:${s.name}`,lv:"red",t:`${m.name}: ${s.name} ${s.state=="failed"?"failed":"is down"}`,go:"#mc-"+m.key}))});
 const la=minsAgo(LIVE&&LIVE.fetched);
 if(la==null||la>B2CFG.live[0]){const r=la==null||la>B2CFG.live[1];out.push({id:`live:${(LIVE&&LIVE.fetched)||"none"}`,lv:r?"red":"yellow",t:`Today, Waiting and Routines are ${la==null?"missing":"from "+agoT(LIVE.fetched)}. The refresh should update them twice a day.`,go:'.sec[data-sec="today"]'})}
 (LIVE.routines||[]).filter(r=>r.last_status=="failed"&&!r.paused).forEach(r=>out.push({id:`rtn:${r.name}:${r.last_run||""}`,lv:"red",t:`Routine failed: ${r.name}${r.last_run?` (${fmt(r.last_run)})`:""}`,go:"#rtn"}));
 const o={red:0,yellow:1};return out.sort((a,b)=>o[a.lv]-o[b.lv])}
function snoozed(){const s=ld(SK,{}),n=Date.now();let ch=0;for(const k in s)if(!(s[k]>n)){delete s[k];ch=1}if(ch)sv(SK,s);return s}
function tomorrow8(){const d=new Date();d.setDate(d.getDate()+1);d.setHours(8,0,0,0);return d.getTime()}
function paintAlerts(){let el=$2("#b2al");if(!el){el=document.createElement("div");el.id="b2al";el.setAttribute("role","region");el.setAttribute("aria-label","Alerts");const w=$2(".wrap"),h=w&&w.querySelector("header");if(h)h.after(el);else document.body.prepend(el)}
 const A=alerts(),S=snoozed(),live=A.filter(a=>!S[a.id]),zn=A.length-live.length;
 if(!A.length){el.hidden=true;el.innerHTML="";return}
 el.hidden=false;el.className="b2al"+(live.some(a=>a.lv=="red")?" red":live.length?" yellow":" calm");
 el.innerHTML=(live.length?`<ul>${live.map(a=>`<li class="lv-${a.lv}" data-id="${esc(a.id)}"><i class="d-${a.lv}" aria-hidden="true"></i><button type="button" class="b2go" data-go="${esc(a.go||"")}">${esc(a.t)}</button><span class="b2sn"><button type="button" data-sn="4">Snooze ${B2CFG.snoozeH}h</button><button type="button" data-sn="t">Until tomorrow</button></span></li>`).join("")}</ul>`:"")+
  `<div class="b2f">${live.length>1?`<button type="button" data-sn="all">Snooze all ${B2CFG.snoozeH}h</button>`:""}${zn?`<button type="button" data-un="1">${zn} snoozed · show</button>`:""}<small>Snooze is saved on this device only.</small></div>`}
document.addEventListener("click",e=>{const el=$2("#b2al");if(!el||!el.contains(e.target))return;const S=snoozed();
 const g=e.target.closest("[data-go]");if(g&&g.dataset.go){const t=$2(g.dataset.go);if(t){if(t.tagName=="DETAILS")t.open=true;t.scrollIntoView({behavior:"smooth",block:"start"});try{t.focus({preventScroll:true})}catch(x){}}return}
 const b=e.target.closest("[data-sn]");if(b){const until=b.dataset.sn=="t"?tomorrow8():Date.now()+B2CFG.snoozeH*36e5;
  const ids=b.dataset.sn=="all"?alerts().map(a=>a.id):[b.closest("li").dataset.id];ids.forEach(i=>S[i]=until);sv(SK,S);paintAlerts();toast(`Snoozed until ${fmt(until)} on this device`);return}
 if(e.target.closest("[data-un]")){sv(SK,{});paintAlerts()}});
function toastNew(){const S=snoozed(),seen=(()=>{try{return JSON.parse(sessionStorage.getItem(TK)||"[]")}catch(e){return[]}})();
 const n=alerts().filter(a=>a.lv=="red"&&!S[a.id]&&!seen.includes(a.id));if(!n.length)return;
 toast(n.length==1?"⚠ "+n[0].t:`⚠ ${n.length} alerts need attention`,1);try{sessionStorage.setItem(TK,JSON.stringify(seen.concat(n.map(a=>a.id))))}catch(e){}}

/* ---------- Desk progress refresh: run history (read-only) ---------- */
function paintHist(){const H=LIVE.routine_history,host=$2("#rtn");if(!H||!host)return;let el=$2("#b2rh");if(!el){el=document.createElement("div");el.id="b2rh";el.className="b2rh";host.appendChild(el)}
 const R=(H.runs||[]).slice(0,8),sk=R.filter(r=>!r.live_json).length,P=LIVE.parts||{};
 el.innerHTML=`<h3>${esc(H.name)} · last ${R.length} runs</h3><p class="b2m">Read-only. Taken from the backup files each run leaves behind.${sk?` <b class="bad">${sk} of ${R.length} skipped the live panels.</b>`:""}</p>
 <ol>${R.map(r=>`<li><span class="b2t">${esc(fmt(r.at))}</span><span class="b2p ok">Projects ✓</span><span class="b2p ${r.live_json?"ok":"bad"}">${r.live_json?"Live panels ✓":"Live panels skipped"}</span></li>`).join("")}</ol>
 ${P.routines?`<p class="b2m">Routine list as of ${esc(fmt(P.routines))}${minsAgo(P.routines)>B2CFG.live[1]?" (old: the refresh hasn't updated it)":""}.</p>`:""}`}

/* ---------- teammate badges from desk-log recency ---------- */
function paintTeam(){const T=LIVE.teammates||[],TA=LIVE.team_activity||{};document.querySelectorAll("#tml .tm").forEach((c,i)=>{const x=T[i];if(!x||c.querySelector(".b2tb"))return;
 const cands=[TA[x.name],x.updated].filter(okd).sort((a,b)=>new Date(b)-new Date(a)),last=cands[0],h=last?minsAgo(last)/60:null;
 let lv,w;if(x.on_hold&&String(x.on_hold)!="false"){lv="grey";w="On hold"}else if(h==null){lv="red";w="No desk-log activity"}else if(h<=B2CFG.team[0]){lv="green";w="Active "+agoT(last)}else if(h<=B2CFG.team[1]){lv="yellow";w="Quiet · last "+agoT(last)}else{lv="red";w="Inactive · last "+agoT(last)}
 const b=document.createElement("span");b.className="b2tb lv-"+lv;b.title=`Desk-log activity: ${last?fmt(last)+"":"none"}. Green within ${B2CFG.team[0]}h, yellow within ${B2CFG.team[1]}h.`;b.innerHTML=`<i class="d-${lv}" aria-hidden="true"></i>${esc(w)}`;
 const nm=c.querySelector("b");if(nm)nm.after(b);else c.prepend(b)})}

window.B2={alerts,paintAlerts,onOrg(){}};
paintAlerts();paintHist();paintTeam();setTimeout(toastNew,800);
setInterval(paintAlerts,6e4);
})();
