/* ===== Desk themes (theme.js) =====
 Runs in <head> before first paint. Palettes are CSS variables on <html data-pal="…">; every panel (Team panel too) reads var(--bg|--bg2|--card|--bd|--fg|--fg2|--mut|--acc|--acc-s|--on-acc|--track|--c-*|--p-*).
 Choice is kept in localStorage "desk-pal" ({id, custom:{bg,card,bd,acc,fg}}) and synced by the Desk helper like the other desk-* keys.
 A legacy appearance.accent (old Accent setting) with no saved theme shows as Custom with that accent; it is written only when you change the theme. */
(function(){
var PAL=/*PAL_BEGIN*/{"classic":{"light":{"bg":"#f3f4f7","bg2":"#e9ecf2","card":"#ffffff","bd":"#e2e5eb","fg":"#14171c","fg2":"#3b424d","mut":"#5f6876","acc":"#2559d4","acc-s":"#e8effd","on-acc":"#ffffff","track":"#e8ebf0","c-active":"#2559d4","c-done":"#15803d","c-blocked":"#dc2626","c-hold":"#a67a04","p-active-bg":"#e6eefe","p-active":"#1e4fc2","p-done-bg":"#dcf5e5","p-done":"#126b34","p-blocked-bg":"#fde4e4","p-blocked":"#a71d1d","p-hold-bg":"#fbf0cf","p-hold":"#835e00"},"dark":{"bg":"#0c0e12","bg2":"#12151b","card":"#161a21","bd":"#252a33","fg":"#e9ecf1","fg2":"#c3c9d3","mut":"#8c95a3","acc":"#6a9bff","acc-s":"#1a2640","on-acc":"#0c0e12","track":"#262b35","c-active":"#6a9bff","c-done":"#34d27b","c-blocked":"#f26464","c-hold":"#f0be3c","p-active-bg":"#1a2640","p-active":"#9dbcff","p-done-bg":"#12301f","p-done":"#7ee3a6","p-blocked-bg":"#361819","p-blocked":"#ff9c9c","p-hold-bg":"#33290e","p-hold":"#f3cf6e"}},"spring":{"light":{"bg":"#f2f7ef","bg2":"#e4eedf","card":"#ffffff","bd":"#d3e2cc","fg":"#18261b","fg2":"#344a39","mut":"#56685a","acc":"#b02e66","acc-s":"#fbe7ef","on-acc":"#ffffff","track":"#e1ebdc","c-active":"#b02e66","c-done":"#2f8a3e","c-blocked":"#d1343b","c-hold":"#b07d07","p-active-bg":"#fbe7ef","p-active":"#8c1f4f","p-done-bg":"#ddf3dc","p-done":"#1f6a2c","p-blocked-bg":"#fde4e4","p-blocked":"#a11d24","p-hold-bg":"#faf0cc","p-hold":"#7a5700"},"dark":{"bg":"#0e140f","bg2":"#131b15","card":"#18211a","bd":"#2a382d","fg":"#e8f2e9","fg2":"#c3d4c6","mut":"#93a897","acc":"#f590b9","acc-s":"#3a1c29","on-acc":"#1a0d13","track":"#26332a","c-active":"#f590b9","c-done":"#6fd884","c-blocked":"#f26a6a","c-hold":"#eec04a","p-active-bg":"#3a1c29","p-active":"#ffb3d1","p-done-bg":"#15331c","p-done":"#93e9a4","p-blocked-bg":"#3a1a1b","p-blocked":"#ffa3a3","p-hold-bg":"#352b0f","p-hold":"#f4d47a"}},"summer":{"light":{"bg":"#fcf7ec","bg2":"#f4ead4","card":"#ffffff","bd":"#e9dcc0","fg":"#1b2230","fg2":"#3a4455","mut":"#5f6878","acc":"#0b6f93","acc-s":"#e1f2f8","on-acc":"#ffffff","track":"#efe5d0","c-active":"#0b6f93","c-done":"#24894a","c-blocked":"#d2382f","c-hold":"#c27c00","p-active-bg":"#e1f2f8","p-active":"#07546f","p-done-bg":"#dcf3e2","p-done":"#17663a","p-blocked-bg":"#fde3df","p-blocked":"#a3231b","p-hold-bg":"#fdeccb","p-hold":"#7d5000"},"dark":{"bg":"#0a1418","bg2":"#0f1b21","card":"#132229","bd":"#22363f","fg":"#e9f4f8","fg2":"#c0d6df","mut":"#8ea9b4","acc":"#4ec6ea","acc-s":"#123444","on-acc":"#04161d","track":"#1f333c","c-active":"#4ec6ea","c-done":"#4fd98a","c-blocked":"#ff6b5e","c-hold":"#ffc247","p-active-bg":"#123444","p-active":"#8ddcf4","p-done-bg":"#113222","p-done":"#86ebb0","p-blocked-bg":"#3b1a17","p-blocked":"#ffaaa1","p-hold-bg":"#382a0c","p-hold":"#ffd785"}},"fall":{"light":{"bg":"#f8f1e8","bg2":"#efe2d2","card":"#fffdf9","bd":"#e5d4be","fg":"#2a1c12","fg2":"#4a382a","mut":"#6e5a49","acc":"#a8461a","acc-s":"#fbe8dc","on-acc":"#ffffff","track":"#eedfcd","c-active":"#a8461a","c-done":"#4f7d23","c-blocked":"#c0302a","c-hold":"#b37400","p-active-bg":"#fbe8dc","p-active":"#83350f","p-done-bg":"#e6f0d6","p-done":"#3d6119","p-blocked-bg":"#fbe1dd","p-blocked":"#9b231e","p-hold-bg":"#fbedcd","p-hold":"#764d00"},"dark":{"bg":"#14100c","bg2":"#1a1510","card":"#211a14","bd":"#3a2e23","fg":"#f4ebe1","fg2":"#d8c8b8","mut":"#a99380","acc":"#f29a5c","acc-s":"#3b2414","on-acc":"#1d0f05","track":"#33281e","c-active":"#f29a5c","c-done":"#9ccc5a","c-blocked":"#f0675d","c-hold":"#efb840","p-active-bg":"#3b2414","p-active":"#ffbd8f","p-done-bg":"#24311a","p-done":"#bde38a","p-blocked-bg":"#3d1c19","p-blocked":"#ffa49c","p-hold-bg":"#382b10","p-hold":"#f5d27e"}},"winter":{"light":{"bg":"#edf2f8","bg2":"#dfe7f1","card":"#ffffff","bd":"#d0dbe8","fg":"#121d30","fg2":"#33435a","mut":"#56657b","acc":"#3554b0","acc-s":"#e5ebfa","on-acc":"#ffffff","track":"#dde5ef","c-active":"#3554b0","c-done":"#1d8466","c-blocked":"#cc3344","c-hold":"#a87708","p-active-bg":"#e5ebfa","p-active":"#263f8c","p-done-bg":"#d9f2ea","p-done":"#14614b","p-blocked-bg":"#fbe3e6","p-blocked":"#9c1f2e","p-hold-bg":"#f8efd2","p-hold":"#735200"},"dark":{"bg":"#0a0f1e","bg2":"#0f1527","card":"#141b30","bd":"#252f4a","fg":"#e7edf8","fg2":"#c1cce2","mut":"#8e9bb7","acc":"#93b4ff","acc-s":"#1d2a4f","on-acc":"#0a1124","track":"#222c45","c-active":"#93b4ff","c-done":"#4fd6b0","c-blocked":"#ff6f80","c-hold":"#f2c55c","p-active-bg":"#1d2a4f","p-active":"#b6ccff","p-done-bg":"#10302a","p-done":"#8ae8cd","p-blocked-bg":"#3b1820","p-blocked":"#ffa8b3","p-hold-bg":"#342b12","p-hold":"#f6d88f"}},"hacker":{"dark":{"bg":"#030603","bg2":"#071007","card":"#0a140b","bd":"#1b3d20","fg":"#5cff8a","fg2":"#3fe06f","mut":"#2fb85a","acc":"#00ff66","acc-s":"#0f2e17","on-acc":"#001a09","track":"#123019","c-active":"#00e5ff","c-done":"#5cff8a","c-blocked":"#ff5c5c","c-hold":"#ffd24d","p-active-bg":"#06262b","p-active":"#6ef2ff","p-done-bg":"#0f2e17","p-done":"#7dffa3","p-blocked-bg":"#2e0d0d","p-blocked":"#ff8a8a","p-hold-bg":"#2b2408","p-hold":"#ffe07a"}}}/*PAL_END*/;
var IDS=["classic","spring","summer","fall","winter","hacker"],NAMES={classic:"Desk (default)",spring:"Spring",summer:"Summer",fall:"Fall",winter:"Winter",hacker:"Hacker / Dark",custom:"Custom"};
var FIXED={hacker:"dark"},K="desk-pal",R=document.documentElement,HX=/^#[0-9a-f]{6}$/i,VARS=Object.keys(PAL.classic.light);
function LS(){try{return window.localStorage}catch(e){return null}}
function hx(h){h=String(h||"").toLowerCase();return HX.test(h)?h:""}
function rgb(h){return [1,3,5].map(function(i){return parseInt(h.substr(i,2),16)})}
function toHex(a){return "#"+a.map(function(v){v=Math.max(0,Math.min(255,Math.round(v)));return (v<16?"0":"")+v.toString(16)}).join("")}
function lum(h){var c=rgb(h).map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)});return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]}
function cr(a,b){var x=lum(a),y=lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)}
function mix(a,b,t){var x=rgb(a),y=rgb(b);return toHex(x.map(function(v,i){return v+(y[i]-v)*t}))}
/* push colour c toward black or white until it reaches ratio r against every colour in bgs */
function ensure(c,bgs,r){var ok=function(x){return bgs.every(function(b){return cr(x,b)>=r})};if(ok(c))return c;
 var mn=function(x){return Math.min.apply(null,bgs.map(function(b){return cr(x,b)}))},t=mn("#000000")>=mn("#ffffff")?"#000000":"#ffffff";for(var i=1;i<=20;i++){var x=mix(c,t,i/20);if(ok(x))return x}return t}
function isDarkNow(){var t=R.dataset.theme;if(R.dataset.palFixed){t=null;try{t=LS().getItem("desk-theme")}catch(e){}}return t?t=="dark":!!(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches)}
/* Custom: user gives bg, card, bd (card border), acc, fg (optional). Everything else is derived and contrast-checked. */
function derive(c){var bg=hx(c.bg)||"#f3f4f7",card=hx(c.card)||"#ffffff",acc=hx(c.acc)||"#2559d4",dark=lum(card)<0.18,
 fg=hx(c.fg)||(cr("#14171c",card)*cr("#14171c",bg)>=cr("#f2f4f7",card)*cr("#f2f4f7",bg)?"#14171c":"#f2f4f7"),
 bg2=mix(bg,fg,0.05),B;fg=c.fg?fg:ensure(fg,[card,bg,bg2],4.5);B=PAL.classic[lum(fg)>0.5?"dark":"light"];var p={bg:bg,bg2:bg2,card:card,fg:fg};
 p.bd=hx(c.bd)||mix(card,fg,0.13);p.fg2=ensure(mix(fg,card,0.18),[card,bg,bg2],4.5);p.mut=ensure(mix(fg,card,0.42),[card,bg,bg2],4.5);
 p.acc=acc;p["acc-s"]=mix(card,acc,0.16);p["on-acc"]=cr("#ffffff",acc)>=cr("#111111",acc)?"#ffffff":"#111111";p.track=mix(card,fg,0.1);
 ["active","done","blocked","hold"].forEach(function(s){var cc=s=="active"?acc:B["c-"+s];p["c-"+s]=ensure(cc,[card,bg],3);
  p["p-"+s+"-bg"]=mix(card,p["c-"+s],0.16);p["p-"+s]=ensure(B["p-"+s],[p["p-"+s+"-bg"],card],4.5);p["p-"+s+"-bg"]=ensure(p["p-"+s+"-bg"],[p["p-"+s]],4.5)});
 p.mode=lum(fg)>0.5?"dark":"light";return p}
function decl(p){var s=VARS.map(function(k){return "--"+k+":"+p[k]}).join(";");var d=(p.mode||"")=="dark"||lum(p.card)<0.18;
 return s+";--line:"+p.bd+";--sh:"+(d?"0 1px 2px rgba(0,0,0,.4)":"0 1px 2px rgba(16,24,40,.05),0 4px 14px rgba(16,24,40,.05)")+";--shh:"+(d?"0 10px 28px rgba(0,0,0,.5)":"0 2px 4px rgba(16,24,40,.06),0 12px 28px rgba(16,24,40,.12)")}
function presetCSS(){var o="";IDS.forEach(function(id){var P=PAL[id],sel="html:root[data-pal="+id+"]";
 if(P.light){o+=sel+"{"+decl(P.light)+"}";if(P.dark)o+=sel+"[data-theme=dark]{"+decl(P.dark)+"}@media(prefers-color-scheme:dark){"+sel+":not([data-theme=light]){"+decl(P.dark)+"}}"}
 else o+=sel+"{"+decl(P.dark)+"}"});return o}
/* resolved palette for a preset in the current light/dark mode */
function resolved(id){var P=PAL[id]||PAL.classic;return (FIXED[id]?P.dark:(isDarkNow()&&P.dark?P.dark:P.light||P.dark))}
function norm(s){var o={id:"classic",custom:null};if(s&&typeof s=="object"){if(s.id=="custom"||IDS.indexOf(s.id)>=0)o.id=s.id;
 if(s.custom&&typeof s.custom=="object"){o.custom={};["bg","card","bd","acc","fg"].forEach(function(k){o.custom[k]=hx(s.custom[k])})}}
 if(o.id=="custom"&&!(o.custom&&o.custom.bg&&o.custom.card&&o.custom.acc))o.id="classic";return o}
function legacyAccent(lay){try{var a=(lay||JSON.parse((LS()||{}).getItem&&LS().getItem("desk-layout")||"null")||{}).appearance||{};return hx(a.accent)}catch(e){return ""}}
function fromAccent(a){var b=resolved("classic");return {bg:b.bg,card:b.card,bd:b.bd,acc:a,fg:""}}
var ST,SAVED=false,STY=null;
function read(){var s=null;try{s=JSON.parse(LS().getItem(K)||"null")}catch(e){}SAVED=!!s;ST=norm(s);
 if(!SAVED){var a=legacyAccent();if(a){ST={id:"custom",custom:fromAccent(a),migrated:true}}}}
function style(){if(!STY){STY=document.getElementById("thm-css");if(!STY){STY=document.createElement("style");STY.id="thm-css";(document.head||R).appendChild(STY)}}return STY}
var BASE=presetCSS(),CUR=null;
function paint(st,preview){st=st||ST;var id=st.id,R_=R,fx=null,css=BASE;
 if(id=="custom"){CUR=derive(st.custom);css+="html:root[data-pal=custom]{"+decl(CUR)+"}";fx=CUR.mode}else{CUR=resolved(id);fx=FIXED[id]||null}
 style().textContent=css;R_.dataset.pal=id;
 if(fx){R_.dataset.palFixed=fx;R_.dataset.theme=fx}
 else if(R_.dataset.palFixed){delete R_.dataset.palFixed;var t=null;try{t=LS().getItem("desk-theme")}catch(e){}if(t)R_.dataset.theme=t;else delete R_.dataset.theme}
 try{var m=document.querySelector('meta[name="theme-color"]');if(m)m.content=CUR.bg}catch(e){}
 try{if(!preview&&typeof paintTT=="function")paintTT()}catch(e){}}
function save(){try{LS().setItem(K,JSON.stringify({id:ST.id,custom:ST.custom}))}catch(e){}SAVED=true;delete ST.migrated}
read();paint();
/* ---------- settings panel (Appearance popover) ---------- */
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function sw(id){var p=id=="custom"?derive(ST.custom||fromAccent(resolved("classic").acc)):resolved(id);
 return '<span class="thsw" style="background:'+p.bg+'"><i style="background:'+p.card+';border-color:'+p.bd+'"><b style="background:'+p.acc+'"></b><u style="background:'+p.fg+'"></u><u style="background:'+p.mut+'"></u></i></span>'}
function grade(r,t){return '<b class="'+(r>=t?"ok":"bad")+'">'+r.toFixed(1)+':1 '+(r>=t?"✓":"✗")+'</b>'}
function report(p){return 'Text '+grade(Math.min(cr(p.fg,p.card),cr(p.fg,p.bg)),4.5)+' · Muted '+grade(Math.min(cr(p.mut,p.card),cr(p.mut,p.bg)),4.5)+' · Accent text '+grade(Math.min(cr(p.acc,p.card),cr(p.acc,p["acc-s"])),4.5)+' · Button '+grade(cr(p["on-acc"],p.acc),4.5)}
function custHTML(){var c=ST.custom,auto=!c.fg,p=derive(c),f=function(k,l){return '<label class="thf"><input type="color" data-thc="'+k+'" value="'+(k=="fg"?p.fg:hx(c[k])||p[k])+'"'+(k=="fg"&&auto?" disabled":"")+'> '+l+'</label>'};
 return '<div class="thcu">'+f("bg","Background")+f("card","Cards")+f("bd","Card border")+f("acc","Accent")+f("fg","Text")+
 '<label class="ck thf"><input type="checkbox" data-thauto'+(auto?" checked":"")+'> Auto text color</label>'+
 '<div class="thcr" aria-live="polite">'+report(p)+'</div>'+
 '<div class="thrs"><label for="thrs">Reset to</label><select id="thrs" data-thbase>'+IDS.map(function(i){return '<option value="'+i+'">'+esc(NAMES[i])+'</option>'}).join("")+'</select><button type="button" class="mbtn" data-threset>Reset</button></div></div>'}
function inner(){return '<div class="thg" role="radiogroup" aria-label="Theme">'+IDS.concat(["custom"]).map(function(id){var on=ST.id==id;
 return '<button type="button" role="radio" aria-checked="'+on+'" class="thb'+(on?" on":"")+'" data-thp="'+id+'">'+sw(id)+'<span>'+esc(NAMES[id])+'</span></button>'}).join("")+'</div>'+
 (ST.id=="custom"?custHTML():'')+'<p class="thn">'+(ST.id=="hacker"?"Hacker is always dark.":ST.id=="custom"?"Custom sets light or dark from your colors.":"Follows the light / dark setting below.")+(ST.migrated?" Your old accent color was carried over.":"")+'</p>'}
function panel(){return '<label>Theme</label><div class="thm" id="thm">'+inner()+'</div>'}
function rerender(){var el=document.getElementById("thm");if(el)el.innerHTML=inner()}
function choose(id){if(id=="custom"){if(!ST.custom||!ST.custom.bg){var b=resolved(ST.id=="custom"?"classic":ST.id);ST.custom={bg:b.bg,card:b.card,bd:b.bd,acc:b.acc,fg:""}}}
 ST.id=id;save();paint();rerender();try{typeof paintTT=="function"&&paintTT()}catch(e){}}
function readInputs(){var el=document.getElementById("thm"),c={bg:"",card:"",bd:"",acc:"",fg:""};if(!el)return ST.custom;
 [].forEach.call(el.querySelectorAll("[data-thc]"),function(i){c[i.dataset.thc]=hx(i.value)});var a=el.querySelector("[data-thauto]");if(a&&a.checked)c.fg="";return c}
document.addEventListener("click",function(e){var b=e.target.closest&&e.target.closest("#thm button");if(!b)return;
 if(b.dataset.thp){choose(b.dataset.thp);return}
 if("threset" in b.dataset){var s=document.querySelector("#thm [data-thbase]"),r=resolved(s?s.value:"classic");ST.custom={bg:r.bg,card:r.card,bd:r.bd,acc:r.acc,fg:""};save();paint();rerender()}});
document.addEventListener("input",function(e){var t=e.target;if(!t.closest||!t.closest("#thm")||!t.dataset||!("thc" in t.dataset))return;
 var c=readInputs();paint({id:"custom",custom:c},true);var r=document.querySelector("#thm .thcr");if(r)r.innerHTML=report(CUR)});
document.addEventListener("change",function(e){var t=e.target;if(!t.closest||!t.closest("#thm"))return;
 if("thc" in t.dataset||"thauto" in t.dataset){ST.custom=readInputs();save();paint();rerender()}});
window.__deskTheme={panel:panel,apply:function(lay){if(!SAVED){var a=legacyAccent(lay);if(a&&ST.id=="classic"){ST={id:"custom",custom:fromAccent(a),migrated:true}}}paint()},
 get:function(){return {id:ST.id,custom:ST.custom,saved:SAVED,palette:CUR}},set:function(id,c){if(c)ST.custom=c;choose(id)},
 presets:PAL,ids:IDS,names:NAMES,derive:derive,contrast:cr};
})();
