/* ===== Desk features: org filter, "as of" stamps, machines panel, command palette. Vanilla JS, ideas only (see NOTICE). ===== */
(function(){
const $1=s=>document.querySelector(s),A=k=>B1ART[k]||"";
/* thresholds in minutes. Machines + header pill: Stale after 10, Not updating after 30. Twice-daily panels use their refresh interval. */
const B1CFG={header:[10,30],machines:[10,30],live:[13*60,26*60],projects:[48*60,7*24*60]};
const tP=d=>new Date(d).toLocaleTimeString("en-US",{timeZone:TZ,hour:"numeric",minute:"2-digit"});
const dP=d=>new Date(d).toLocaleDateString("en-CA",{timeZone:TZ});
function asofTxt(iso){ // "As of 3:07 PM" / "As of Mon 10:20 PM" / "As of Oct 23, 7:08 PM"
 const d=new Date(iso),n=new Date(),days=(new Date(dP(n))-new Date(dP(d)))/864e5;
 if(days<=0)return tP(d);if(days<7)return d.toLocaleDateString("en-US",{timeZone:TZ,weekday:"short"})+" "+tP(d);
 return d.toLocaleDateString("en-US",{timeZone:TZ,month:"short",day:"numeric"})+", "+tP(d)}
function ago(iso){const m=Math.max(0,Math.round((Date.now()-new Date(iso))/6e4));if(m<1)return"just now";if(m<60)return m+" min ago";const h=Math.round(m/60);if(h<48)return h+(h==1?" hr ago":" hr ago");return Math.round(h/24)+" days ago"}
const ok=iso=>iso&&!isNaN(new Date(iso));
function stamp(iso,th){ // -> {cls,html,title}
 if(!ok(iso))return{cls:"",html:A("clock")+"<span>Not updated yet</span>",title:"Times are in your local time zone."};
 const m=(Date.now()-new Date(iso))/6e4,cls=m>=th[1]?"dead":m>=th[0]?"stale":"",tag=cls=="dead"?" · Not updating":cls=="stale"?" · Stale":"";
 return{cls,html:(cls?A("clock-stale"):A("clock"))+`<span>As of ${esc(asofTxt(iso))} · ${esc(ago(iso))}${tag}</span>`,
  title:new Date(iso).toLocaleString("en-US",{timeZone:TZ,dateStyle:"medium",timeStyle:"short"})+""+(cls?", may be out of date":"")+". Times are in your local time zone."}}
const AS=(DATA&&DATA.asof)||{},newest=(...a)=>a.filter(ok).sort((x,y)=>new Date(y)-new Date(x))[0]||null;
const SRC={live:()=>LIVE.fetched,projects:()=>newest(AS.updates,AS.status),machines:()=>MACH&&(MACH.listed_at||MACH.generated_at)};
const PANELS={today:"live",waiting:"live",routsum:"live",routines:"live",teammates:"live",activity:"live",projects:"projects"};
function paintStamps(){
 const hd=newest(SRC.live(),SRC.projects(),SRC.machines()),h=stamp(hd,B1CFG.header),p=$1("#asofp");
 if(p){p.className="asofp "+h.cls;p.innerHTML=h.html;p.title=h.title+" Newest data on Desk."}
 for(const[id,src]of Object.entries(PANELS)){const sec=document.querySelector(`.sec[data-sec="${id}"]`);if(!sec)continue;
  let el=sec.querySelector(":scope > .asof");if(!el){el=document.createElement("p");el.className="asof";el.setAttribute("aria-live","off");sec.appendChild(el)}
  const s=stamp(SRC[src](),B1CFG[src]);el.className="asof "+s.cls;el.innerHTML=s.html;el.title=s.title}
 const ms=$1("#mach-asof");if(ms){const s=stamp(SRC.machines(),B1CFG.machines);ms.className="asof "+s.cls;ms.innerHTML=s.html;ms.title=s.title}}
/* ---------- org chips ---------- */
const openN=k=>(DATA.areas[k]||[]).filter(p=>p.status!="done").length;
function paintOrgs(){const g=$1("#orgf");if(!g)return;const ks=areaKeys(),sel=ORGSEL.filter(x=>ks.includes(x));
 const chip=(k,lab,n,on,tip)=>`<button type="button" class="orgc" data-o="${esc(k)}"${k=="all"||k=="Personal"?"":` data-oi="${areaKeys().indexOf(k)%4+1}"`} aria-pressed="${on}" tabindex="-1" title="${esc(tip||"")}"><span class="ck" aria-hidden="true">${A("status-ok")}</span><span class="sw" aria-hidden="true"></span>${esc(lab)}<span class="ct">${n}</span></button>`;
 g.innerHTML=chip("all","All",ks.reduce((a,k)=>a+openN(k),0),!sel.length,"Show every organisation")+ks.map(k=>chip(k,AREAS[k]||k,openN(k),sel.includes(k),(DATA.org_tips||{})[k])).join("");
 const bs=[...g.querySelectorAll(".orgc")],cur=bs.find(b=>b.getAttribute("aria-pressed")=="true")||bs[0];if(cur)cur.tabIndex=0}
function setOrg(next){ORGSEL=next;try{next.length?localStorage.setItem("desk-org",JSON.stringify(next)):localStorage.removeItem("desk-org")}catch(e){}render();if(typeof rToday=="function")rToday();if(window.B2&&B2.onOrg)B2.onOrg();paintOrgs();
 const n=visKeys().length;(typeof say=="function"?say:()=>{})(next.length?`Showing ${next.map(k=>AREAS[k]||k).join(", ")}`:"Showing all organisations");return n}
const og=$1("#orgf");if(og){og.addEventListener("click",e=>{const b=e.target.closest(".orgc");if(!b)return;const k=b.dataset.o;
  if(k=="all"){setOrg([]);}else if(e.shiftKey||e.metaKey||e.ctrlKey){const s=new Set(ORGSEL);s.has(k)?s.delete(k):s.add(k);setOrg([...s])}else setOrg(ORGSEL.length==1&&ORGSEL[0]==k?[]:[k]);
  const nb=og.querySelector(`.orgc[data-o="${CSS.escape(k)}"]`);nb&&nb.focus()});
 og.addEventListener("keydown",e=>{const bs=[...og.querySelectorAll(".orgc")],i=bs.indexOf(document.activeElement);if(i<0)return;let j=null;
  if(e.key=="ArrowRight"||e.key=="ArrowDown")j=(i+1)%bs.length;else if(e.key=="ArrowLeft"||e.key=="ArrowUp")j=(i-1+bs.length)%bs.length;else if(e.key=="Home")j=0;else if(e.key=="End")j=bs.length-1;
  if(j!=null){e.preventDefault();bs.forEach(b=>b.tabIndex=-1);bs[j].tabIndex=0;bs[j].focus()}})}
/* ---------- machines panel ---------- */
const PILL={online:["Online","status-ok"],quiet:["Quiet","status-wait"],asleep:["Asleep","status-dash"],offline:["Offline","status-x"],unknown:["Unknown","status-dash"],snapshot:["Snapshot","status-wait"]};
function seenTxt(m){const s=m.last_seen;if(m.state=="online")return s?`Checked in ${ago(s)}.`:"Online.";
 if(m.state=="quiet"||m.state=="asleep")return s?`No check-in for ${ago(s).replace(" ago","")}. Probably asleep.`:"Probably asleep.";
 return s?`Last seen ${ago(s)}.`:"Never checked in."}
const fresh=(iso,min)=>ok(iso)&&(Date.now()-new Date(iso))/6e4<min;
function disk(pct,lv,asof){if(pct==null||pct==="")return`<div class="mdisk lv-grey">Disk —</div>`;
 return`<div class="mdisk lv-${esc(lv||"green")}" title="${asof?esc("Checked "+asofTxt(asof)+""):""}">Disk ${+pct}% used${asof?` · as of ${esc(asofTxt(asof))}`:""}<div class="bar" role="img" aria-label="Disk ${+pct}% used"><i style="width:${Math.min(100,+pct)}%"></i><s></s></div></div>`}
function svc(list,asof,th){if(!list||!list.length)return"";const st=!fresh(asof,(th&&th.probe_fresh_min)||30);
 return`<div class="msv${st?" stale":""}" title="${st?esc(`Last checked ${asof?asofTxt(asof):"never"}; may be out of date.`):""}">${list.map(s=>{const lv=s.level||"grey",word=s.note||s.state;
  return`<span title="${esc(s.name+(s.port?" :"+s.port:"")+" · "+word)}"><i class="d-${esc(st&&lv!="grey"?"grey":lv)}" aria-hidden="true"></i>${esc(s.name)}${s.port?`<small>&nbsp;:${+s.port}</small>`:""}<span class="sr-only"> ${esc(word)}</span></span>`}).join("")}</div>`}
function card(m,stat){const st=stat?(m.state=="unknown"?"unknown":"snapshot"):(m.state||"unknown"),[lab,g]=PILL[st]||PILL.unknown,lv=m.level||"grey";
 const pillLv=stat?lv:(m.state=="online"&&lv=="red"?"green":lv);
 let body=stat?`<div class="mseen">${ok(m.as_of)?`Snapshot as of ${esc(asofTxt(m.as_of))}`:"No snapshot yet."}${m.source?` · ${esc(m.source)}`:""}</div>`:`<div class="mseen">${esc(seenTxt(m))}</div>`;
 body+=disk(m.disk_pct,m.disk_level||(m.disk_pct>=90?"red":m.disk_pct>=80?"yellow":"green"),stat?null:m.disk_as_of);
 body+=stat?(m.addons?`<div class="msv">${m.addons.map(a=>`<span title="${esc(a.name+" · "+a.state+(a.update?" · update available":""))}"><i class="d-${esc(a.level||"grey")}" aria-hidden="true"></i>${esc(a.name)}<span class="sr-only"> ${esc(a.state)}</span></span>`).join("")}</div>`:""):svc(m.services,m.services_as_of,MACH.thresholds);
 if(!stat&&m.heartbeat&&ok(m.heartbeat.at)){const h=m.heartbeat,up=h.uptime_s?(h.uptime_s>=86400?Math.floor(h.uptime_s/86400)+"d ":"")+Math.floor(h.uptime_s%86400/3600)+"h":"";
  body+=`<p class="mhb" title="${esc("Heartbeat #"+h.seq+" from the read-only status reporter on this machine (optional heartbeat, every 5 min)")}">Heartbeat · ${esc(ago(h.at))}${up?` · up ${esc(up)}`:""}${h.load!=null?` · load ${esc(String(Array.isArray(h.load)?h.load[0]:h.load))}`:""}${h.power?` · ${esc(h.power)}`:""}</p>`}
 if(m.updates&&m.updates.length)body+=`<p class="mnote">${esc(m.updates.join(" · "))}</p>`;
 if(m.pinned)body+=`<p class="mpin">${esc(m.pinned)}</p>`;
 (m.notes||[]).forEach(n=>body+=`<p class="mnote">${esc(n)}</p>`);
 return`<article class="mcard lv-${esc(lv)}" id="mc-${esc(m.key)}" data-mk="${esc(m.key)}" tabindex="-1"><div class="mtop"><span class="mico" aria-hidden="true">${A(m.icon||"server")}</span><div class="mnm"><b>${esc(m.name)}</b><small>${esc(m.role||"")}</small></div><span class="mpill lv-${esc(pillLv)}">${A(g)}${esc(lab)}</span></div>${body}</article>`}
function paintMachines(){const el=$1("#machines");if(!el)return;
 if(!MACH||!Array.isArray(MACH.machines)||!MACH.machines.length){el.innerHTML=`<h2 id="mach-h">Machines</h2><p class="asof" id="mach-asof"></p><p class="mempty">No machines connected yet.</p>`;return}
 const ms=MACH.machines,off=ms.filter(m=>m.state=="offline").length;
 el.innerHTML=`<h2 id="mach-h">Machines<span class="sum">${off?`${off} of ${ms.length} offline`:`${ms.length} tracked`}</span></h2><p class="asof" id="mach-asof"></p><div class="mgrid">${ms.map(m=>card(m,false)).join("")}${(MACH.static||[]).map(m=>card(m,true)).join("")}</div>${MACH.note?`<p class="mnote">${esc(MACH.note)}</p>`:""}`}
/* ---------- command palette (⌘K / Ctrl+K) ---------- */
const ov=document.createElement("div");ov.className="kpo";ov.hidden=true;
ov.innerHTML=`<div class="kp" role="dialog" aria-modal="true" aria-label="Command palette"><div class="kpi">${A("search")}<input id="kpq" type="text" role="combobox" aria-expanded="true" aria-controls="kpl" aria-autocomplete="list" autocomplete="off" spellcheck="false" placeholder="Type a command or search…" aria-label="Type a command or search"></div><ul class="kpl" id="kpl" role="listbox" aria-label="Results"></ul><div class="kpf"><span><kbd>↑</kbd> <kbd>↓</kbd> to move</span><span><kbd>↵</kbd> to open</span><span><kbd>esc</kbd> to close</span></div></div>`;
document.body.appendChild(ov);
const KQ=ov.querySelector("#kpq"),KL=ov.querySelector("#kpl");let KI=[],KS=0,KMODE=null,KF=null;
const go=(sel,open)=>{const s=document.querySelector(sel);if(!s)return;const d=s.closest("details")||s.querySelector("details");if(open&&d)d.open=true;s.scrollIntoView({behavior:"smooth",block:"start"});(s.querySelector("h2,summary")||s).focus?.({preventScroll:true})};
function actions(){return[
 {s:"Actions",t:"Go to Projects",run:()=>go('.sec[data-sec="projects"]')},
 {s:"Actions",t:"Go to Routines",run:()=>go('.sec[data-sec="routines"]',true)},
 {s:"Actions",t:"Go to Approvals",k2:"Waiting on you",run:()=>go('.sec[data-sec="waiting"]')},
 {s:"Actions",t:"Go to Machines",run:()=>go('.sec[data-sec="machines"]')},
 {s:"Actions",t:"Filter by org…",sub:"org"},
 {s:"Actions",t:"Add a tile",run:()=>{const b=$1("#tadd");if(b){b.scrollIntoView({block:"center"});b.click()}}},
 {s:"Actions",t:"Edit layout",run:()=>$1("#edt")?.click()},
 {s:"Actions",t:"Run a routine now…",sub:"routine"},
 {s:"Actions",t:"Check for update",k2:"Reload Desk",run:()=>location.reload()},
 {s:"Actions",t:`Ask ${BOTN()}…`,run:q=>{const i=$1("#aq");if(!i)return;go('.sec[data-sec="ask"]');if(q)i.value=q;setTimeout(()=>i.focus(),50)},ask:true},
 {s:"Actions",t:"Toggle theme",run:()=>$1("#tt")?.click()}]}
function items(){if(KMODE=="org")return[{s:"Filter by org",t:"All organisations",run:()=>setOrg([])}].concat(areaKeys().map(k=>({s:"Filter by org",t:AREAS[k]||k,k2:openN(k)+" open",org:k,run:()=>setOrg([k])})));
 if(KMODE=="routine")return(LIVE.routines||[]).filter(r=>!r.trigger||r.trigger=="schedule").map(r=>({s:"Run a routine now",t:r.name,k2:r.paused?"paused":(r.schedule||""),run:()=>{
  if(!confirm(`Run "${r.name}" now? This sends a message to ${BOTN()}.`))return;const row=[...document.querySelectorAll("#rtl .rr")].find(x=>x.dataset.n==r.name),b=row&&row.querySelector('[data-ra="run-now"]');if(b)b.click();else toast("Couldn't find that routine on the page.")}}));
 const P=[];for(const k of Object.keys(DATA.areas||{}))for(const p of DATA.areas[k])P.push({s:"Projects",t:p.name,k2:(AREAS[k]||k)+" · "+p.status,org:k,hay:[p.next_step,p.summary,p.owner].join(" "),run:()=>openM(k+"::"+p.name)});
 const T=(LIVE.teammates||[]).map(m=>({s:"Agents",t:m.name,k2:m.role||"",hay:[m.doing,m.waiting_on].join(" "),run:()=>{const d=$1("#tmv");if(d)d.open=true;go('.sec[data-sec="teammates"]')}}));
 const M=MACH?[...(MACH.machines||[]),...(MACH.static||[])].map(m=>({s:"Machines",t:m.name,k2:(PILL[m.state]||PILL.unknown)[0],run:()=>{go('.sec[data-sec="machines"]');setTimeout(()=>document.getElementById("mc-"+m.key)?.focus({preventScroll:true}),300)}})):[];
 return P.concat(T,M,actions())}
function score(it,q){if(!q)return 1;const t=it.t.toLowerCase(),h=(it.k2+" "+(it.hay||"")).toLowerCase();
 if(t.startsWith(q))return 100;const i=t.indexOf(q);if(i>=0)return 80-i/10;if(h.includes(q))return 30;
 let j=0;for(const c of t){if(c==q[j])j++;if(j==q.length)return 10}return 0}
function hl(t,q){const i=q?t.toLowerCase().indexOf(q):-1;return i<0?esc(t):esc(t.slice(0,i))+`<mark class="kq">${esc(t.slice(i,i+q.length))}</mark>`+esc(t.slice(i+q.length))}
function paintK(){const q=KQ.value.trim().toLowerCase();let L=items().map(it=>({it,sc:score(it,q)})).filter(x=>x.sc>0);
 if(L.some(x=>x.sc>=30))L=L.filter(x=>x.sc>=30);if(q)L.sort((a,b)=>b.sc-a.sc);const ord=["Projects","Agents","Machines","Actions"];
 if(!q&&!KMODE)L=L.filter(x=>x.it.s=="Actions"||x.it.s=="Machines");
 const ask=actions().find(a=>a.ask);if(q&&!KMODE)L.push({it:Object.assign({},ask,{t:`Ask ${BOTN()}: “${KQ.value.trim()}”`,q:KQ.value.trim()}),sc:1});
 const grp={};L.forEach(x=>(grp[x.it.s]=grp[x.it.s]||[]).push(x.it));const oi=g=>ord.indexOf(g),ks=Object.keys(grp).sort((a,b)=>oi(a)-oi(b));
 KI=[];let h="";for(const g of ks){h+=`<li class="kh" role="presentation">${esc(g)}</li>`;for(const it of grp[g].slice(0,q?8:12)){const i=KI.push(it)-1;
  h+=`<li role="option" id="kpo${i}" data-i="${i}" aria-selected="false">${it.org?`<span class="ksw" style="background:var(--org-${areaKeys().indexOf(it.org)%4+1},var(--mut))"></span>`:""}<span>${hl(it.t,q)}</span>${it.k2?`<span class="k2">${esc(it.k2)}</span>`:""}</li>`}}
 const only=KI.length==1&&KI[0].ask&&q;KL.innerHTML=KI.length?(only?`<li class="kpe" role="presentation">No matches.</li>`:"")+h:`<li class="kpe" role="presentation">No matches.</li>`;KS=0;selK()}
function selK(){KL.querySelectorAll("[role=option]").forEach(o=>{const on=+o.dataset.i==KS;o.setAttribute("aria-selected",on);if(on)o.scrollIntoView({block:"nearest"})});KQ.setAttribute("aria-activedescendant",KI.length?"kpo"+KS:"")}
function runK(i){const it=KI[i];if(!it)return;if(it.sub){KMODE=it.sub;KQ.value="";KQ.placeholder=it.t;paintK();return}closeK();it.run&&it.run(it.q)}
function openK(){if(!ov.hidden)return;KF=document.activeElement;KMODE=null;KQ.value="";KQ.placeholder="Type a command or search…";ov.hidden=false;paintK();KQ.focus()}
function closeK(){ov.hidden=true;KMODE=null;KF&&KF.focus&&document.contains(KF)&&KF.focus({preventScroll:true})}
KQ.addEventListener("input",paintK);
KQ.addEventListener("keydown",e=>{if(e.key=="ArrowDown"){e.preventDefault();KS=Math.min(KI.length-1,KS+1);selK()}else if(e.key=="ArrowUp"){e.preventDefault();KS=Math.max(0,KS-1);selK()}
 else if(e.key=="Enter"){e.preventDefault();runK(KS)}else if(e.key=="Escape"){e.preventDefault();if(KMODE){KMODE=null;KQ.value="";KQ.placeholder="Type a command or search…";paintK()}else closeK()}
 else if(e.key=="Backspace"&&!KQ.value&&KMODE){KMODE=null;KQ.placeholder="Type a command or search…";paintK()}else if(e.key=="Tab")e.preventDefault()});
KL.addEventListener("mousemove",e=>{const o=e.target.closest("[role=option]");if(o&&+o.dataset.i!=KS){KS=+o.dataset.i;selK()}});
KL.addEventListener("click",e=>{const o=e.target.closest("[role=option]");if(o)runK(+o.dataset.i)});
ov.addEventListener("mousedown",e=>{if(e.target===ov)closeK()});
document.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&!e.altKey&&(e.key=="k"||e.key=="K")){e.preventDefault();ov.hidden?openK():closeK()}},true);
const kb=$1("#kbtn");if(kb){kb.querySelector(".ki").innerHTML=A("search");if(!/Mac|iPhone|iPad/.test(navigator.platform||navigator.userAgent))kb.querySelector("kbd").textContent="Ctrl K";kb.onclick=openK}
const ap=$1("#asofp");if(ap)ap.onclick=()=>go('.sec[data-sec="machines"]');
/* ---------- boot ---------- */
const _r=render;render=function(){_r.apply(this,arguments);try{paintStamps()}catch(e){}};
paintOrgs();render();paintMachines();paintStamps();setInterval(()=>{paintStamps();paintMachines()},60000);
window.__deskB1={openK,closeK,setOrg,B1CFG};
})();
