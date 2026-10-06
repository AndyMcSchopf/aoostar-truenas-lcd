"use strict";
let L,V,S,T,H={},IMG={},pi=0,ei=-1,scale=1,imageMode=false;
let inspectorToken=0;
function uid(){return "e_"+Date.now().toString(36)+"_"+Math.random().toString(36).slice(2,9)}

function selectedId(){return ei>=0&&P().elements[ei]?P().elements[ei].id:null}
function indexById(id){if(!id)return -1;return P().elements.findIndex(e=>e.id===id)}
function byId(id){let i=indexById(id);return i>=0?P().elements[i]:null}
const $=x=>document.getElementById(x),ACC=["orange","amber","violet","blue","pink"];async function J(u,o){let r=await fetch(u,o);if(!r.ok)throw Error(await r.text());return r.json()}const P=()=>L.panels[pi],E=()=>P().elements[ei],TH=()=>T[L.theme]||T["lcars-orange"],C=a=>TH()[a]||TH().orange,SNAP=n=>$("snap").checked?Math.round(n/10)*10:Math.round(n);
const TEXTCOL=[["auto","AUTO"],["white","WEISS"],["muted","GRAU"],["orange","ORANGE"],["amber","AMBER"],["violet","VIOLETT"],["blue","BLAU"],["pink","PINK"],["green","GRÜN"]];
function textColor(v,t){if(!v||v==="auto"||v==="white")return t.text;if(v==="muted")return t.muted||"#aaa";if(v==="green")return"#66cc99";return C(v)}
function fresh(){return{name:"NEUES PANEL",duration:6,background:"",image:{mode:"cover",x:0,y:0,zoom:1},elements:[{id:uid(),type:"lcars_header",text:"NEUES PANEL",x:18,y:14,w:924,h:42,accent:"orange"}]}}
async function init(){[L,V,S,T,H]=await Promise.all([J("/api/layout"),J("/api/values"),J("/api/sensors"),J("/api/themes"),J("/api/history")]);L=window.AOOSTAR_LAYOUT.migrate(L);if(!L.panels.length)L.panels=[fresh()];ensureIds();wire();render();save();loadImages();setInterval(refresh,5000)}
function wire(){const pal=[["TEXT","text"],["LCARS CARD","card"],["STATUS","badge"],["BALKEN","bar"],["KURVE","sparkline"],["TRENNER","line"]];$("palette").innerHTML=pal.map(x=>`<button data-t="${x[1]}">${x[0]}</button>`).join("");$("palette").onclick=e=>e.target.dataset.t&&add(e.target.dataset.t);$("addPanel").onclick=()=>{L.panels.push(fresh());pi=L.panels.length-1;ei=-1;render();save()};$("dupPanel").onclick=()=>{let q=structuredClone(P());(q.elements||[]).forEach(e=>e.id=uid());L.panels.splice(pi+1,0,q);pi++;ei=-1;render();save()};$("delPanel").onclick=()=>{if(L.panels.length>1&&confirm("Panel löschen?")){L.panels.splice(pi,1);pi=Math.max(0,pi-1);ei=-1;render();save()}};$("leftPanel").onclick=()=>movePanel(-1);$("rightPanel").onclick=()=>movePanel(1);$("panelName").onchange=()=>{P().name=$("panelName").value;renderPanels();save()};$("duration").onchange=()=>{P().duration=+$("duration").value;save()};$("search").oninput=renderSensors;$("theme").onchange=()=>{L.theme=$("theme").value;renderCanvas();save()};$("save").onclick=save;$("upload").onclick=()=>$("file").click();$("file").onchange=upload;$("imgMode").onclick=()=>{imageMode=!imageMode;$("imgMode").textContent="BILDPOSITION: "+(imageMode?"EIN":"AUS");$("imgMode").classList.toggle("active",imageMode)};$("removeBg").onclick=()=>{P().background="";renderCanvas();save()};["fit","zoom","imgX","imgY"].forEach(id=>$(id).onchange=imageProps);$("preview").onclick=async()=>{await save();let x=await J("/api/lcd/generate",{method:"POST"});status(x.ok?`Vorschau: ${x.panels} Panels`:x.error)};$("activate").onclick=async()=>{if(confirm("LCD-Konfiguration sichern und aktivieren?")){let x=await J("/api/lcd/activate",{method:"POST"});status(x.ok?"LCD-Konfiguration aktiviert – Neustart/Reload erforderlich":x.error)}};addEventListener("resize",fit);addEventListener("keydown",keys);$("canvas").onmousedown=bgDrag}
function add(t){let z={id:uid(),type:t,x:80,y:80,accent:"orange"};if(t==="text")Object.assign(z,{text:"TEXT",size:24});if(t==="card")Object.assign(z,{text:"GRUPPE",w:300,h:150});if(t==="badge")Object.assign(z,{label:"truenas_system_status",w:110,h:32});if(t==="bar")Object.assign(z,{label:"cpu_usage_percent",w:250,h:14,max:100});if(t==="sparkline")Object.assign(z,{label:"cpu_usage_percent",w:250,h:80,max:100});if(t==="line")Object.assign(z,{w:250,h:3});P().elements.push(z);ei=P().elements.length-1;renderCanvas();inspect();save()}
function movePanel(d){let n=pi+d;if(n<0||n>=L.panels.length)return;[L.panels[pi],L.panels[n]]=[L.panels[n],L.panels[pi]];pi=n;render();save()}
function ensureIds(){
 const seen=new Set();
 (L?.panels||[]).forEach(p=>(p.elements||[]).forEach(e=>{
   if(!e.id||seen.has(e.id))e.id=uid();
   seen.add(e.id);
 }));
}
function render(){ensureIds();renderPanels();renderTheme();renderSensors();renderCanvas();inspect();syncImage();fit()}
function renderPanels(){$("panels").innerHTML=L.panels.map((p,i)=>`<button class="${i===pi?"active":""}" data-i="${i}">${i+1} ${p.name}</button>`).join("");$("panels").onclick=e=>{if(e.target.dataset.i!==undefined){pi=+e.target.dataset.i;ei=-1;render()}};$("panelName").value=P().name;$("duration").value=P().duration}
function renderTheme(){$("theme").innerHTML=Object.entries(T).map(([k,v])=>`<option value="${k}">${v.name}</option>`).join("");$("theme").value=L.theme}
function renderSensors(){let q=$("search").value.toLowerCase();$("sensors").innerHTML=S.filter(x=>(x.name+x.id).toLowerCase().includes(q)).map(x=>`<div class=sensor data-id="${x.id}"><b>${x.name}</b><br><span class=muted>${x.value}</span></div>`).join("");$("sensors").onclick=e=>{let n=e.target.closest(".sensor");if(n){P().elements.push({id:uid(),type:"sensor",label:n.dataset.id,title:n.dataset.id,x:80,y:90,w:82,h:36,size:24,unit:"",align:"center",titleAlign:"left"});ei=P().elements.length-1;renderCanvas();inspect();save()}}}
function renderCanvas(){
 let c=$("canvas"),t=TH(),m=P().image,bg=P().background,d=bg?IMG[bg]:null;
 c.style.backgroundColor=t.bg;c.style.backgroundImage=bg?`url('/user-images/${encodeURIComponent(bg)}')`:"none";
 c.style.backgroundRepeat="no-repeat";
 if(bg&&d){
  let r=window.AOOSTAR_LAYOUT.imageRect(d.w,d.h,m.mode,m.zoom,m.x,m.y);
  c.style.backgroundSize=`${r.w}px ${r.h}px`;
  c.style.backgroundPosition=`${r.left}px ${r.top}px`;
 }else{
  c.style.backgroundSize="auto";c.style.backgroundPosition="0 0";
 }
 c.innerHTML=P().elements.map((z,i)=>html(z,i,t)).join("");
 c.querySelectorAll(".obj").forEach(n=>{n.onclick=e=>{e.stopPropagation();if(document.activeElement&&document.activeElement.blur)document.activeElement.blur();ei=+n.dataset.i;renderCanvas();inspect()};n.onmousedown=drag});
 addResizeHandles();
}

function lcdValue(z,val,native){
 if(!native)return val;
 if(z.label==="truenas_uptime"){
  let m=String(val??"").match(/(?:(\d+)\s+day[s]?,?\s*)?(\d+):(\d+):/i);
  return m?((+(m[1]||0)*24)+(+m[2]))+"h "+(+m[3])+"m":val;
 }
 // String-valued semantics must never be parsed as numbers.
 if(z.label==="truenas_version"||z.label==="truenas_pools_healthy_de"||
    z.label==="truenas_net_down"||z.label==="truenas_net_up"||
    z.label==="truenas_system_status") return val;
 // LCD uses integer presentation for percentage/temperature telemetry.
 if(/(?:usage_percent|temperature)/.test(z.label||"") && isFinite(parseFloat(val)))
   return Math.round(parseFloat(val));
 return val;
}

function sensorBox(z){let size=Number(z.size)||24,w=Number(z.w)||Math.max(72,Math.round(size*3.4)),h=Number(z.h)||Math.max(34,Math.round(size*1.45));return{w,h};}
function cssAlign(a){return a==="right"?"right":a==="left"?"left":"center";}
function html(z,i,t){let s=`left:${z.x}px;top:${z.y}px;`,cl=`obj ${i===ei?"selected":""}`,a=C(z.accent),native=[0,2,3].includes(pi);if(z.type==="header"||z.type==="lcars_header")return`<div class="${cl}" data-i="${i}" style="${s}width:${z.w}px;height:${z.h}px;border-radius:22px;background:${a};color:#111;padding:12px 18px;font-weight:bold">${z.text}</div>`;if(z.type==="card")return`<div class="${cl} card" data-i="${i}" style="${s}width:${z.w}px;height:${z.h}px"><div class=cardhead style="background:${a};color:${textColor(z.textColor||"auto",t)};font-size:${z.size||15}px">${z.text}</div></div>`;if(z.type==="sensor"){let val=lcdValue(z,V[z.label]??"–",native),b=sensorBox(z),ta=cssAlign(z.titleAlign||"left"),va=cssAlign(z.align||"center");return`<div class="${cl} sensorobj" data-i="${i}" style="${s}width:${b.w}px;height:${b.h}px;font-size:${z.size}px;font-weight:${native?"700":"400"};color:${textColor(z.valueColor||"auto",t)}"><span class=label style="color:${textColor(z.titleColor||"muted",t)};font-size:${z.titleSize||Math.max(15,Math.min(18,Math.round((z.size||24)*.48)))}px" style="text-align:${ta}">${z.title||""}</span><div class=sensorval style="text-align:${va}">${val} ${z.unit||""}</div></div>`;}if(z.type==="bar"){if(native)return"";let n=parseFloat(V[z.label]||0),q=Math.max(0,Math.min(100,n/(z.max||100)*100));return`<div class="${cl} bar" data-i="${i}" style="${s}width:${z.w}px;height:${z.h}px"><div style="height:100%;width:${q}%;background:${a}"></div></div>`}if(z.type==="sparkline")return spark(z,i,a);if(z.type==="badge")return native?`<div class="${cl}" data-i="${i}" style="${s}width:${z.w}px;height:${z.h}px;color:${t.text};font-size:22px;font-weight:700;text-align:center">${V[z.label]??"–"}</div>`:`<div class="${cl}" data-i="${i}" style="${s}width:${z.w}px;height:${z.h}px;border:2px solid #66cc99;border-radius:18px;color:#66cc99;text-align:center;padding:6px">${V[z.label]??"–"}</div>`;if(z.type==="line")return`<div class="${cl}" data-i="${i}" style="${s}width:${z.w}px;height:${z.h}px;background:${a}"></div>`;if(z.type==="text")return`<div class="${cl}" data-i="${i}" style="${s}font-size:${z.size}px;color:${textColor(z.textColor||"auto",t)}">${z.text}</div>`;return""}
function spark(z,i,a){let v=(H[z.label]||[]).slice(-60),w=z.w,h=z.h;if(v.length<2)return`<div class="obj ${i===ei?"selected":""}" data-i="${i}" style="left:${z.x}px;top:${z.y}px;width:${w}px;height:${h}px;border-bottom:2px solid ${a}"><span class=muted>Verlauf sammelt Daten…</span></div>`;let nums=v.map(x=>+x.value||+x),mx=z.max||Math.max(...nums,1),pts=nums.map((n,k)=>`${k/(nums.length-1)*w},${h-Math.max(0,Math.min(1,n/mx))*h}`).join(" "),area=`0,${h} ${pts} ${w},${h}`;return`<svg class="obj ${i===ei?"selected":""}" data-i="${i}" style="left:${z.x}px;top:${z.y}px" width="${w}" height="${h}"><polygon points="${area}" fill="${a}" class=sparkfill/><polyline points="${pts}" fill="none" stroke="${a}" stroke-width="3"/></svg>`}
function canResize(z){return z.type==="sensor"||["header","lcars_header","card","badge","bar","sparkline","line"].includes(z.type)}
function effectiveWH(z){if(z.type==="sensor"){let b=sensorBox(z);return{w:b.w,h:b.h}}return{w:Number(z.w)||0,h:Number(z.h)||0}}
function addResizeHandles(){
 if(ei<0)return;
 let n=$("canvas").querySelector(`.obj[data-i="${ei}"]`),z=E();
 if(!n||!canResize(z))return;
 ["nw","n","ne","e","se","s","sw","w"].forEach(d=>{
   let h=document.createElement("span");h.className="resize-handle rh-"+d;h.dataset.dir=d;
   h.onmousedown=resizeStart;n.appendChild(h);
 });
}
function resizeStart(ev){
 ev.preventDefault();ev.stopPropagation();
 let editId=selectedId(),z=byId(editId);if(!z)return;let dir=ev.currentTarget.dataset.dir,b=effectiveWH(z),
     sx=ev.clientX,sy=ev.clientY,ox=Number(z.x)||0,oy=Number(z.y)||0,ow=b.w,oh=b.h;
 // Persist effective sensor defaults as soon as visual resizing starts.
 if(z.w===undefined)z.w=ow;if(z.h===undefined)z.h=oh;
 function mv(e){
   let dx=(e.clientX-sx)/scale,dy=(e.clientY-sy)/scale,nx=ox,ny=oy,nw=ow,nh=oh;
   if(dir.includes("e"))nw=SNAP(Math.max(24,ow+dx));
   if(dir.includes("s"))nh=SNAP(Math.max(18,oh+dy));
   if(dir.includes("w")){nx=SNAP(ox+dx);nw=SNAP(Math.max(24,ow-dx));if(nw===24)nx=ox+ow-24}
   if(dir.includes("n")){ny=SNAP(oy+dy);nh=SNAP(Math.max(18,oh-dy));if(nh===18)ny=oy+oh-18}
   z.x=nx;z.y=ny;z.w=nw;z.h=nh;renderCanvas();updateInspectorGeometry();
 }
 function up(){removeEventListener("mousemove",mv);removeEventListener("mouseup",up);inspect();save()}
 addEventListener("mousemove",mv);addEventListener("mouseup",up);
}
function field(label,id,value,attrs=""){return`<label class=prop-field><span>${label}</span><input id="${id}" value="${value??""}" ${attrs}></label>`}
function selectField(label,id,options,value){return`<label class=prop-field><span>${label}</span><select id="${id}">${options.map(([v,n])=>`<option value="${v}" ${v===value?"selected":""}>${n}</option>`).join("")}</select></label>`}
function group(title,body){return`<div class=prop-group><div class=prop-title>${title}</div>${body}</div>`}
function inspect(){
 inspectorToken++;
 if(ei<0){$("inspector").innerHTML='<div class="prop-empty">Element auswählen.</div>';return}
 let z=E(),editId=z.id,token=inspectorToken,b=effectiveWH(z),res=canResize(z),htmls="";
 htmls+=group("ELEMENT",field("Typ","itype",z.type,"disabled")+field(z.type==="sensor"?"Überschrift":"Text / Titel","it",z.text??z.title??""));
 htmls+=group("POSITION & GRÖSSE",'<div class=prop-grid4>'+field("X","ix",z.x,'type="number"')+field("Y","iy",z.y,'type="number"')+field("Breite","iw",res?b.w:0,`type="number" min="24" ${res?"":"disabled"}`)+field("Höhe","ih",res?b.h:0,`type="number" min="18" ${res?"":"disabled"}`)+'</div>'+(res?'<div class=prop-hint>Größe auch direkt im Editor an den Griffen ändern.</div>':""));
 let textProps="";
 if(["sensor","text","card","header","lcars_header"].includes(z.type))textProps+=field(z.type==="sensor"?"Wert Größe":"Schriftgröße","isz",Number(z.size)||(z.type==="card"?15:(z.type==="header"||z.type==="lcars_header"?18:24)),'type="number" min="8" max="96" step="1"');
 if(z.type==="sensor"){textProps+=field("Überschrift Größe","itsz",Number(z.titleSize)||Math.max(15,Math.min(18,Math.round((Number(z.size)||24)*.48))),'type="number" min="8" max="48" step="1"');textProps+=selectField("Überschrift Farbe","itc",TEXTCOL,z.titleColor||"muted");textProps+=selectField("Wert Farbe","ivc",TEXTCOL,z.valueColor||"auto");textProps+=selectField("Überschrift ausrichten","ita",[["left","LINKS"],["center","MITTIG"],["right","RECHTS"]],z.titleAlign||"left");textProps+=selectField("Wert ausrichten","iva",[["left","LINKS"],["center","MITTIG"],["right","RECHTS"]],z.align||"center")}
 else if(["text","card","header","lcars_header"].includes(z.type))textProps+=selectField("Schriftfarbe","itc",TEXTCOL,z.textColor||"auto");
 if(textProps)htmls+=group("TEXT",textProps);
 htmls+=group("DARSTELLUNG",selectField("Akzentfarbe","ia",ACC.map(a=>[a,a.toUpperCase()]),z.accent||"orange"));
 htmls+=group("ANORDNUNG",'<div class=prop-actions><button id=front>VORNE</button><button id=back>HINTEN</button><button id=dup>DUPLIZIEREN</button><button id=del>LÖSCHEN</button></div>');
 $("inspector").innerHTML=htmls;
 const commit=(ev)=>{if(token!==inspectorToken)return;let target=byId(editId);if(!target)return;applyTo(target,ev?.target?.id)};
 ["it","ix","iy","iw","ih","isz","itsz","itc","ivc","ia","ita","iva"].forEach(id=>{let el=$(id);if(!el)return;el.oninput=(["ix","iy","iw","ih","isz","itsz","it"].includes(id))?commit:null;el.onchange=commit});
 $("dup").onclick=()=>{let src=byId(editId);if(!src)return;let q=structuredClone(src);q.id=uid();q.x+=10;q.y+=10;P().elements.push(q);ei=P().elements.length-1;renderCanvas();inspect();save()};
 $("del").onclick=()=>{let idx=indexById(editId);if(idx<0)return;P().elements.splice(idx,1);ei=-1;renderCanvas();inspect();save()};
 $("front").onclick=()=>layerById(editId,1);$("back").onclick=()=>layerById(editId,-1)
}
function updateInspectorGeometry(){
 let z=E(),b=effectiveWH(z);
 if($("ix"))$("ix").value=Math.round(z.x);if($("iy"))$("iy").value=Math.round(z.y);
 if($("iw"))$("iw").value=Math.round(b.w);if($("ih"))$("ih").value=Math.round(b.h);
}
function applyTo(z,sourceId){
 if(!z)return;
 if(sourceId==="it"){if(z.text!==undefined)z.text=$("it").value;if(z.title!==undefined)z.title=$("it").value}
 if(sourceId==="ix")z.x=+$("ix").value;if(sourceId==="iy")z.y=+$("iy").value;
 if(canResize(z)&&sourceId==="iw")z.w=Math.max(24,+$("iw").value||24);
 if(canResize(z)&&sourceId==="ih")z.h=Math.max(18,+$("ih").value||18);
 if(sourceId==="isz"&&["sensor","text","card","header","lcars_header"].includes(z.type))z.size=Math.max(8,Math.min(96,+$("isz").value||24));
 if(sourceId==="itsz"&&z.type==="sensor")z.titleSize=Math.max(8,Math.min(48,+$("itsz").value||15));
 if(sourceId==="itc"){if(z.type==="sensor")z.titleColor=$("itc").value;else z.textColor=$("itc").value}
 if(sourceId==="ivc"&&z.type==="sensor")z.valueColor=$("ivc").value;
 if(sourceId==="ia")z.accent=$("ia").value;
 if(z.type==="sensor"&&sourceId==="ita")z.titleAlign=$("ita").value;
 if(z.type==="sensor"&&sourceId==="iva")z.align=$("iva").value;
 renderCanvas();save()
}
function layerById(id,d){let a=P().elements,idx=indexById(id),n=idx+d;if(idx<0||n<0||n>=a.length)return;[a[idx],a[n]]=[a[n],a[idx]];ei=n;renderCanvas();inspect();save()}
function drag(ev){
 if(imageMode||ev.target.classList.contains("resize-handle"))return;
 ev.preventDefault();ei=+ev.currentTarget.dataset.i;
 let editId=P().elements[ei]?.id,z=byId(editId);if(!z)return;
 let sx=ev.clientX,sy=ev.clientY,ox=z.x,oy=z.y;
 function mv(e){z.x=SNAP(ox+(e.clientX-sx)/scale);z.y=SNAP(oy+(e.clientY-sy)/scale);renderCanvas();updateInspectorGeometry()}
 function up(){removeEventListener("mousemove",mv);removeEventListener("mouseup",up);inspect();save()}
 addEventListener("mousemove",mv);addEventListener("mouseup",up)
}
function bgDrag(ev){if(!imageMode)return;let m=P().image,sx=ev.clientX,sy=ev.clientY,ox=m.x,oy=m.y;function mv(e){m.x=Math.round(ox+(e.clientX-sx)/scale);m.y=Math.round(oy+(e.clientY-sy)/scale);syncImage();renderCanvas()}function up(){removeEventListener("mousemove",mv);removeEventListener("mouseup",up);save()}addEventListener("mousemove",mv);addEventListener("mouseup",up)}
function keys(e){if(ei<0||["INPUT","SELECT"].includes(document.activeElement.tagName))return;let d=e.shiftKey?10:1;if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(e.key)){e.preventDefault();let z=E();if(e.key==="ArrowLeft")z.x-=d;if(e.key==="ArrowRight")z.x+=d;if(e.key==="ArrowUp")z.y-=d;if(e.key==="ArrowDown")z.y+=d;renderCanvas();inspect();save()}if(e.key==="Delete")$("del")?.click()}
function imageProps(){let m=P().image;m.mode=$("fit").value;m.zoom=+$("zoom").value;m.x=+$("imgX").value;m.y=+$("imgY").value;renderCanvas();save()}function syncImage(){let m=P().image;$("fit").value=m.mode;$("zoom").value=m.zoom;$("imgX").value=m.x;$("imgY").value=m.y}
async function upload(){let f=$("file").files[0];if(!f)return;let fd=new FormData();fd.append("image",f);let x=await J("/api/images",{method:"POST",body:fd});P().background=x.file;await save();await loadImages();renderCanvas()}
async function loadImages(){let a=await J("/api/images");IMG=Object.fromEntries(a.map(x=>[x.name,{w:x.width,h:x.height}]));$("images").innerHTML=a.map(x=>`<div class=thumb><img src="/user-images/${encodeURIComponent(x.name)}"><div><b>${x.name}</b><br><span class=muted>${x.width}×${x.height}</span><br><button class=use data-n="${x.name}">NUTZEN</button><button class=rm data-n="${x.name}">LÖSCHEN</button></div></div>`).join("");$("images").onclick=async e=>{let n=e.target.dataset.n;if(!n)return;if(e.target.classList.contains("use")){P().background=n;renderCanvas();save()}else if(e.target.classList.contains("rm")){await J("/api/images/"+encodeURIComponent(n),{method:"DELETE"});if(P().background===n)P().background="";loadImages();renderCanvas();save()}};renderCanvas()}
async function refresh(){V=await J("/api/values");H=await J("/api/history");renderCanvas();let n=Math.max(0,...Object.values(H).map(x=>x.length||0));$("historyInfo").textContent=`VERLAUF: ${n} Messpunkte`}
async function save(){await J("/api/layout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(L)});status("Gespeichert.")}function status(x){$("status").textContent=x}function fit(){scale=Math.min(1,$("viewport").clientWidth/960);$("canvas").style.transform=`scale(${scale})`;$("viewport").style.height=(376*scale)+"px"}init();