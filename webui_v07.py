#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory, Response
from pathlib import Path
from PIL import Image
import json, os, re, time, shutil

app = Flask(__name__)
CFG = Path(os.environ.get("AOOSTAR_CFG", "/app/cfg"))
SENS = CFG / "sensors" / "values.txt"
IMG = CFG / "images"
BACKUP = CFG / "backups"
LAYOUT = CFG / "layout-v07.json"
MONITOR = CFG / "monitor.json"
for p in (CFG, IMG, BACKUP, SENS.parent):
    p.mkdir(parents=True, exist_ok=True)

W, H = 960, 376
THEMES = {
 "lcars-orange":{"name":"LCARS Orange","bg":"#050608","panel":"#111319","orange":"#F29A49","amber":"#F6B85A","violet":"#8E7CC3","blue":"#6699CC","pink":"#C96B9A","text":"#F5EEE6","muted":"#AFA7A0","ok":"#66CC99","warn":"#FFCC66","bad":"#CC6666"},
 "lcars-classic":{"name":"LCARS Classic","bg":"#050608","panel":"#111319","orange":"#FF9966","amber":"#FFCC99","violet":"#9999CC","blue":"#99CCFF","pink":"#CC6699","text":"#FFF4E8","muted":"#B9AFA6","ok":"#66CC99","warn":"#FFCC66","bad":"#CC6666"},
 "enterprise-dark":{"name":"Enterprise Dark","bg":"#090D13","panel":"#18212D","orange":"#E20074","amber":"#FF4FA3","violet":"#8E7CC3","blue":"#55A7FF","pink":"#CC6699","text":"#F7F9FC","muted":"#9EABBA","ok":"#35C98B","warn":"#F5B942","bad":"#F05A67"},
 "mono":{"name":"Monochrom","bg":"#050505","panel":"#171717","orange":"#E8E8E8","amber":"#BDBDBD","violet":"#8F8F8F","blue":"#D0D0D0","pink":"#A5A5A5","text":"#F5F5F5","muted":"#A0A0A0","ok":"#DADADA","warn":"#BDBDBD","bad":"#FFFFFF"}
}
DEFAULT = {
 "version":"0.7.0","theme":"lcars-orange","canvas":{"width":W,"height":H},
 "panels":[
  {"name":"SYSTEM","duration":6,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},
   "elements":[
    {"type":"lcars_header","text":"TRUESTARMAX / SYSTEM 01","x":18,"y":14,"w":924,"h":42,"accent":"orange"},
    {"type":"lcars_elbow","text":"CPU","x":18,"y":72,"w":175,"h":126,"accent":"orange"},
    {"type":"sensor","label":"cpu_usage_percent","title":"AUSLASTUNG","x":218,"y":84,"size":38,"unit":"%"},
    {"type":"sensor","label":"temperature_cpu","title":"TEMPERATUR","x":218,"y":145,"size":28,"unit":"°C"},
    {"type":"bar","label":"cpu_usage_percent","x":218,"y":186,"w":250,"h":14,"max":100,"accent":"orange"},
    {"type":"lcars_elbow","text":"RAM","x":18,"y":216,"w":175,"h":126,"accent":"violet"},
    {"type":"sensor","label":"mem_usage_percent","title":"BELEGUNG","x":218,"y":228,"size":38,"unit":"%"},
    {"type":"sensor","label":"temperature_memory","title":"TEMPERATUR","x":218,"y":289,"size":28,"unit":"°C"},
    {"type":"bar","label":"mem_usage_percent","x":218,"y":330,"w":250,"h":14,"max":100,"accent":"violet"},
    {"type":"lcars_card","text":"NETZWERK","x":500,"y":78,"w":442,"h":120,"accent":"blue"},
    {"type":"sensor","label":"truenas_net_down","title":"DOWNLOAD","x":530,"y":115,"size":25,"unit":""},
    {"type":"sensor","label":"truenas_net_up","title":"UPLOAD","x":735,"y":115,"size":25,"unit":""},
    {"type":"lcars_card","text":"STATUS","x":500,"y":216,"w":442,"h":126,"accent":"amber"},
    {"type":"badge","label":"truenas_system_status","x":530,"y":260,"w":115,"h":34},
    {"type":"sensor","label":"truenas_uptime","title":"LAUFZEIT","x":680,"y":258,"size":21,"unit":""}
   ]},
  {"name":"SPEICHER / ZFS","duration":7,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},
   "elements":[
    {"type":"lcars_header","text":"SPEICHER / ZFS 02","x":18,"y":14,"w":924,"h":42,"accent":"amber"},
    {"type":"pool","index":0,"x":18,"y":76,"w":450,"h":125,"accent":"orange"},
    {"type":"pool","index":1,"x":492,"y":76,"w":450,"h":125,"accent":"violet"},
    {"type":"pool","index":2,"x":18,"y":222,"w":450,"h":125,"accent":"blue"},
    {"type":"pool","index":3,"x":492,"y":222,"w":450,"h":125,"accent":"pink"}
   ]},
  {"name":"TRUENAS","duration":7,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},
   "elements":[
    {"type":"lcars_header","text":"TRUENAS CORE SERVICES 03","x":18,"y":14,"w":924,"h":42,"accent":"orange"},
    {"type":"lcars_card","text":"APPS","x":18,"y":78,"w":300,"h":210,"accent":"violet"},
    {"type":"sensor","label":"truenas_apps_running","title":"AKTIV","x":48,"y":125,"size":38,"unit":""},
    {"type":"sensor","label":"truenas_apps_stopped","title":"GESTOPPT","x":170,"y":130,"size":25,"unit":""},
    {"type":"sensor","label":"truenas_apps_updates","title":"UPDATES","x":48,"y":210,"size":29,"unit":""},
    {"type":"sensor","label":"truenas_apps_crashed","title":"FEHLER","x":170,"y":210,"size":29,"unit":""},
    {"type":"lcars_card","text":"ZFS / SYSTEM","x":342,"y":78,"w":600,"h":210,"accent":"orange"},
    {"type":"sensor","label":"truenas_pools_healthy_de","title":"POOLS","x":375,"y":125,"size":31,"unit":""},
    {"type":"sensor","label":"truenas_scrub_de","title":"SCRUB","x":375,"y":195,"size":17,"unit":""},
    {"type":"badge","label":"truenas_system_status","x":795,"y":110,"w":115,"h":34},
    {"type":"sensor","label":"truenas_version","title":"VERSION","x":375,"y":250,"size":18,"unit":""},
    {"type":"sensor","label":"truenas_uptime","title":"LAUFZEIT","x":18,"y":320,"size":19,"unit":""},
    {"type":"sensor","label":"truenas_model","title":"HARDWARE","x":360,"y":320,"size":17,"unit":""}
   ]},
  {"name":"BILD","duration":10,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},
   "elements":[
    {"type":"lcars_footer","text":"TRUESTARMAX / VISUAL 04","x":18,"y":320,"w":924,"h":40,"accent":"orange"},
    {"type":"badge","label":"truenas_system_status","x":690,"y":323,"w":100,"h":32},
    {"type":"sensor","label":"temperature_cpu","title":"CPU","x":815,"y":327,"size":18,"unit":"°C"}
   ]}
 ]}

ALIASES={"cpu_usage_percent":"CPU – Auslastung","temperature_cpu":"CPU – Temperatur","mem_usage_percent":"RAM – Belegung","temperature_memory":"RAM – Temperatur","temperature_gpu":"GPU – Temperatur","truenas_net_down":"LAN – Download","truenas_net_up":"LAN – Upload","truenas_version":"TrueNAS – Version","truenas_system_status":"TrueNAS – Systemstatus","truenas_apps_running":"Apps – aktiv","truenas_apps_stopped":"Apps – gestoppt","truenas_apps_crashed":"Apps – fehlerhaft","truenas_apps_updates":"Apps – Updates","truenas_pools_healthy":"ZFS – gesunde Pools","truenas_pools_healthy_de":"ZFS – gesunde Pools","truenas_scrub_de":"ZFS – Scrub"}

def values():
    out={}
    if SENS.exists():
        for line in SENS.read_text(errors="replace").splitlines():
            if ":" in line:
                k,v=line.split(":",1); out[k.strip()]=v.strip()
    return out

def friendly(k):
    if k in ALIASES:return ALIASES[k]
    m=re.match(r"truenas_pool_(\d+)_(.+)",k)
    if m:
        names={"name":"Name","status":"Status","healthy":"Gesund","used_percent":"Belegung","used":"Belegt","free":"Frei","size":"Größe","scan":"Scrub"}
        return f"ZFS Pool {int(m.group(1))+1} – {names.get(m.group(2),m.group(2))}"
    if k.startswith("temperature_nvme_"):return "NVMe – "+k.split("_",3)[-1].replace("_"," ")+" – Temperatur"
    if k.startswith("temperature_drivetemp_"):return "HDD – "+k[len("temperature_drivetemp_"):].replace("_"," ")+" – Temperatur"
    return k

def load_layout():
    if not LAYOUT.exists():
        LAYOUT.write_text(json.dumps(DEFAULT,ensure_ascii=False,indent=2))
    try:return json.loads(LAYOUT.read_text())
    except:return DEFAULT

HTML=r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AOOSTAR TrueNAS LCD v0.7</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#050608;color:#F5EEE6;font:14px Arial,sans-serif}header{height:58px;background:#090B0F;display:flex;align-items:center;padding:0 18px;border-bottom:6px solid #F29A49}header b{font-size:17px}.muted{color:#AFA7A0}
main{display:grid;grid-template-columns:280px minmax(600px,1fr) 285px;gap:12px;padding:12px}.pane{background:#0D1016;border:1px solid #262C35;border-radius:16px;padding:11px;margin-bottom:10px}
.btn{background:#171B22;color:#F5EEE6;border:1px solid #343B46;border-radius:18px;padding:7px 11px;margin:2px;cursor:pointer}.btn:hover,.btn.active{background:#F29A49;color:#111;border-color:#F29A49}.canvas{position:relative;width:960px;height:376px;background:#050608;overflow:hidden;transform-origin:top left}.viewport{overflow:hidden;border:1px solid #343B46;background:#050608}.el{position:absolute;cursor:move;user-select:none}.el.sel{outline:2px dashed #F6B85A;outline-offset:2px}.sensor-label{font-size:.52em;color:#AFA7A0;letter-spacing:.08em;display:block}.lcars-card{background:#111319;border-radius:24px;overflow:hidden}.lcars-card .cap{height:30px;padding:6px 16px;color:#111;font-weight:800;letter-spacing:.08em}.lcars-header,.lcars-footer{border-radius:22px;display:flex;align-items:center;padding:0 20px;color:#111;font-weight:900;letter-spacing:.09em}.lcars-elbow{border-radius:30px 0 0 30px;color:#111;font-weight:900;padding:18px}.bar{background:#242932;border-radius:8px;overflow:hidden}.badge{border-radius:18px;border:2px solid #66CC99;color:#66CC99;display:flex;align-items:center;justify-content:center;font-weight:800;background:#0A0D11}.pool{background:#111319;border-radius:22px;overflow:hidden}.pool .head{height:30px;padding:6px 15px;color:#111;font-weight:900}.pool .body{padding:14px 18px}.pool .pct{font-size:30px}.pool .small{color:#AFA7A0}.sensoritem{padding:7px;border-bottom:1px solid #242A33;cursor:pointer}.sensoritem:hover{background:#171B22}input,select{width:100%;background:#090C11;color:#F5EEE6;border:1px solid #343B46;border-radius:8px;padding:7px;margin:3px 0}.row{display:flex;gap:5px}.row>*{flex:1}.tools{display:flex;flex-wrap:wrap}
@media(max-width:1150px){main{grid-template-columns:1fr}}
</style></head><body><header><b>AOOSTAR / TRUESTARMAX</b><span style="margin-left:auto" class="muted">LCARS ORANGE · 960 × 376 · v0.7.0</span></header><main>
<div><div class="pane"><b>PANELS</b><div id="panels"></div><button class="btn" onclick="addPanel()">+ PANEL</button></div><div class="pane"><b>ELEMENTE</b><div class="tools"><button class="btn" onclick="addText()">TEXT</button><button class="btn" onclick="addCard()">LCARS CARD</button><button class="btn" onclick="addBadge()">STATUS</button><button class="btn" onclick="addBar()">BALKEN</button></div></div><div class="pane"><b>SENSOREN</b><input id="q" placeholder="Sensor suchen..." oninput="renderSensors()"><div id="sensors" style="max-height:320px;overflow:auto"></div></div></div>
<div><div class="pane"><div class="row"><input id="pname" onchange="panelProp()"><input id="pdur" type="number" min="1" onchange="panelProp()"><select id="theme" onchange="themeProp()"></select></div><div class="viewport" id="vp"><div class="canvas" id="canvas"></div></div><div class="tools"><button class="btn" onclick="save()">SPEICHERN</button><button class="btn" onclick="file.click()">BILD HOCHLADEN</button><input id="file" type="file" accept="image/*" hidden onchange="upload()"><button class="btn" id="imgedit" onclick="toggleImageEdit()">BILDPOSITION: AUS</button><button class="btn" onclick="removeImage()">BILD LÖSCHEN</button></div><div class="row"><select id="mode" onchange="imageProp()"><option value="contain">EINPASSEN</option><option value="cover">AUSFÜLLEN</option><option value="center">ORIGINAL</option></select><input id="zoom" type="number" min=".25" max="4" step=".05" onchange="imageProp()"><input id="ix" type="number" onchange="imageProp()"><input id="iy" type="number" onchange="imageProp()"></div></div></div>
<div><div class="pane"><b>EIGENSCHAFTEN</b><div id="props" class="muted">Element auswählen.</div></div><div class="pane"><b>BILDER</b><div id="imagelist"></div></div><div class="pane"><b>LCD</b><button class="btn" onclick="prepare()">LCD-KANDIDAT ERZEUGEN</button><div id="status" class="muted"></div></div></div>
</main><script>
"use strict";
let L=null,V={},S=[],T={},pi=0,ei=-1,imgEdit=false,scale=1,HIST={};
const $=id=>document.getElementById(id);
const accents=["orange","amber","violet","blue","pink"];
async function jget(u){const r=await fetch(u);if(!r.ok)throw new Error(u+" HTTP "+r.status);return await r.json();}
function p(){return L.panels[pi]} function e(){return p().elements[ei]}
function th(){return T[L.theme]||T["lcars-orange"]}
function color(a){return th()[a]||th().orange}
function pushHistory(){for(const [k,v] of Object.entries(V)){let n=parseFloat(String(v).replace(",","."));if(!Number.isFinite(n))continue;(HIST[k]??=[]).push(n);if(HIST[k].length>60)HIST[k].shift();}}
async function init(){
 try{
  [L,V,S,T]=await Promise.all([jget("/api/layout"),jget("/api/values"),jget("/api/sensors"),jget("/api/themes")]);pushHistory();
  ensureDefaults();wireStatic();render();await renderImages();addEventListener("resize",fit);
 }catch(err){console.error(err);setStatus("Initialisierung fehlgeschlagen: "+err);}
}
function ensureDefaults(){
 if(!L.theme)L.theme="lcars-orange";
 if(!L.panels||L.panels.length<4)return;
 if(!L.panels[0].elements?.length)L.panels[0].elements=systemDefaults();
 if(!L.panels[1].elements?.length)L.panels[1].elements=zfsDefaults();
 if(!L.panels[2].elements?.length)L.panels[2].elements=trueNasDefaults();
 if(!L.panels[3].elements?.length)L.panels[3].elements=imageDefaults();
}
function systemDefaults(){return [
 {type:"lcars_header",text:"TRUESTARMAX / SYSTEM 01",x:18,y:14,w:924,h:42,accent:"orange"},
 {type:"lcars_card",text:"CPU",x:18,y:76,w:292,h:250,accent:"orange"},
 {type:"sensor",label:"cpu_usage_percent",title:"AUSLASTUNG",x:48,y:122,size:36,unit:"%"},
 {type:"sensor",label:"temperature_cpu",title:"TEMPERATUR",x:178,y:128,size:25,unit:"°C"},
 {type:"bar",label:"cpu_usage_percent",x:48,y:185,w:232,h:13,max:100,accent:"orange"},
 {type:"sparkline",label:"cpu_usage_percent",x:48,y:218,w:232,h:75,accent:"orange",max:100},
 {type:"lcars_card",text:"RAM",x:330,y:76,w:292,h:250,accent:"violet"},
 {type:"sensor",label:"mem_usage_percent",title:"BELEGUNG",x:360,y:122,size:36,unit:"%"},
 {type:"sensor",label:"temperature_memory",title:"TEMPERATUR",x:490,y:128,size:25,unit:"°C"},
 {type:"bar",label:"mem_usage_percent",x:360,y:185,w:232,h:13,max:100,accent:"violet"},
 {type:"sparkline",label:"mem_usage_percent",x:360,y:218,w:232,h:75,accent:"violet",max:100},
 {type:"lcars_card",text:"NETZWERK",x:642,y:76,w:300,h:250,accent:"blue"},
 {type:"sensor",label:"truenas_net_down",title:"DOWNLOAD",x:672,y:122,size:24,unit:""},
 {type:"sensor",label:"truenas_net_up",title:"UPLOAD",x:672,y:174,size:24,unit:""},
 {type:"sparkline",label:"truenas_net_down_bytes_sec",x:672,y:225,w:240,h:68,accent:"blue",auto:true},
 {type:"badge",label:"truenas_system_status",x:812,y:18,w:118,h:32}
]}
function zfsDefaults(){let a=[{type:"lcars_header",text:"SPEICHER / ZFS 02",x:18,y:14,w:924,h:42,accent:"amber"}];["orange","violet","blue","pink"].forEach((c,i)=>a.push({type:"pool",index:i,x:i%2?492:18,y:i<2?76:222,w:450,h:125,accent:c}));return a}
function trueNasDefaults(){return [
 {type:"lcars_header",text:"TRUENAS CORE SERVICES 03",x:18,y:14,w:924,h:42,accent:"orange"},
 {type:"lcars_card",text:"APPS",x:18,y:78,w:300,h:230,accent:"violet"},
 {type:"sensor",label:"truenas_apps_running",title:"AKTIV",x:48,y:128,size:36,unit:""},
 {type:"sensor",label:"truenas_apps_stopped",title:"GESTOPPT",x:172,y:134,size:24,unit:""},
 {type:"bar",label:"truenas_apps_running",x:48,y:188,w:238,h:12,max:19,accent:"violet"},
 {type:"sensor",label:"truenas_apps_updates",title:"UPDATES",x:48,y:226,size:26,unit:""},
 {type:"sensor",label:"truenas_apps_crashed",title:"FEHLER",x:172,y:226,size:26,unit:""},
 {type:"lcars_card",text:"ZFS / SYSTEM",x:340,y:78,w:602,h:230,accent:"orange"},
 {type:"sensor",label:"truenas_pools_healthy_de",title:"POOLS",x:372,y:128,size:30,unit:""},
 {type:"sensor",label:"truenas_scrub_de",title:"SCRUB",x:372,y:192,size:16,unit:""},
 {type:"sensor",label:"truenas_version",title:"VERSION",x:372,y:250,size:18,unit:""},
 {type:"badge",label:"truenas_system_status",x:798,y:110,w:112,h:34},
 {type:"sensor",label:"truenas_uptime",title:"LAUFZEIT",x:18,y:330,size:18,unit:""}
]}
function imageDefaults(){return [{type:"lcars_footer",text:"TRUESTARMAX / VISUAL 04",x:18,y:320,w:924,h:40,accent:"orange"},{type:"badge",label:"truenas_system_status",x:700,y:324,w:100,h:30},{type:"sensor",label:"temperature_cpu",title:"CPU",x:820,y:328,size:18,unit:"°C"}]}
function wireStatic(){
 const q=$("q");if(q)q.addEventListener("input",renderSensors);
 const f=$("file");if(f)f.addEventListener("change",uploadImage);
 const ub=$("uploadBtn");if(ub&&f)ub.onclick=()=>f.click();
 const sv=$("save");if(sv)sv.onclick=save;
 const ie=$("imageEdit");if(ie)ie.onclick=toggleImageEdit;
 const md=$("mode");if(md)md.onchange=imageProp;
 ["zoom","ix","iy"].forEach(id=>{if($(id))$(id).onchange=imageProp});
}
function render(){renderPanels();renderCanvas();renderSensors();renderInspector();fit()}
function fit(){const vp=$("vp");if(!vp)return;scale=Math.min(1,vp.clientWidth/960);$("canvas").style.transform=`scale(${scale})`;vp.style.height=(376*scale)+"px"}
function renderPanels(){const x=$("panels");if(!x)return;x.innerHTML=L.panels.map((z,i)=>`<button class="btn ${i===pi?"active":""}" data-i="${i}">${i+1} ${z.name}</button>`).join("");x.querySelectorAll("button").forEach(b=>b.onclick=()=>{pi=+b.dataset.i;ei=-1;render()});if($("pname"))$("pname").value=p().name;if($("pdur"))$("pdur").value=p().duration;syncImageControls()}
function renderCanvas(){
 const c=$("canvas");if(!c)return;const P=p(),im=P.image||{mode:"cover",x:0,y:0,zoom:1},theme=th();
 c.style.backgroundColor=theme.bg;c.style.backgroundImage=P.background?`url('/user-images/${encodeURIComponent(P.background)}')`:"none";c.style.backgroundRepeat="no-repeat";c.style.backgroundPosition=`${im.x||0}px ${im.y||0}px`;c.style.backgroundSize=im.mode==="contain"?"contain":im.mode==="cover"?`${(im.zoom||1)*100}% auto`:"auto";
 c.innerHTML=(P.elements||[]).map((z,i)=>elementHTML(z,i,theme)).join("");
 c.querySelectorAll("[data-ei]").forEach(n=>{n.onclick=ev=>{ev.stopPropagation();ei=+n.dataset.ei;renderInspector();renderCanvas()};n.onmousedown=ev=>dragElement(ev,+n.dataset.ei)});
}
function elementHTML(z,i,t){const sel=i===ei?"outline:2px dashed "+t.amber+";outline-offset:2px;":"",base=`data-ei="${i}" style="${sel}position:absolute;left:${z.x}px;top:${z.y}px;`;
 if(z.type==="lcars_header"||z.type==="lcars_footer")return `<div ${base}width:${z.w}px;height:${z.h}px;border-radius:22px;background:${color(z.accent)};color:#111;font-weight:900;padding:12px 20px">${z.text}</div>`;
 if(z.type==="lcars_card")return `<div ${base}width:${z.w}px;height:${z.h}px;background:${t.panel};border-radius:22px;overflow:hidden"><div style="height:31px;background:${color(z.accent)};color:#111;font-weight:900;padding:7px 16px">${z.text}</div></div>`;
 if(z.type==="sensor")return `<div ${base}font-size:${z.size}px;color:${t.text}"><span style="display:block;font-size:.52em;color:${t.muted};letter-spacing:.08em">${z.title||""}</span>${V[z.label]??"–"} ${z.unit||""}</div>`;
 if(z.type==="bar"){let n=parseFloat(V[z.label]||0),pct=Math.max(0,Math.min(100,n/(z.max||100)*100));return `<div ${base}width:${z.w}px;height:${z.h}px;background:#242932;border-radius:8px;overflow:hidden"><div style="height:100%;width:${pct}%;background:${color(z.accent)}"></div></div>`}
 if(z.type==="sparkline")return sparkHTML(z,i,t,base);
 if(z.type==="badge"){let v=String(V[z.label]??"–"),ok=/OK|ONLINE/i.test(v),cc=ok?"#66CC99":t.amber;return `<div ${base}width:${z.w}px;height:${z.h}px;border:2px solid ${cc};color:${cc};border-radius:18px;display:flex;align-items:center;justify-content:center;font-weight:800;background:#090B0F">${v}</div>`}
 if(z.type==="pool"){let k=`truenas_pool_${z.index}_`,pct=parseFloat(V[k+"used_percent"]||0),cc=pct>=90?"#CC6666":pct>=75?"#FFCC66":color(z.accent);return `<div ${base}width:${z.w}px;height:${z.h}px;background:${t.panel};border-radius:22px;overflow:hidden"><div style="height:31px;background:${cc};color:#111;font-weight:900;padding:7px 15px">${V[k+"name"]??"POOL"} · ${V[k+"status"]??""}</div><div style="padding:13px 18px"><span style="font-size:30px">${V[k+"used_percent"]??"–"} %</span><span style="margin-left:20px;color:${t.muted}">${V[k+"used"]??""} / ${V[k+"size"]??""}</span><div style="height:11px;background:#242932;border-radius:8px;margin-top:9px;overflow:hidden"><div style="height:100%;width:${pct}%;background:${cc}"></div></div></div></div>`}
 if(z.type==="text")return `<div ${base}font-size:${z.size||24}px;color:${t.text}">${z.text||"TEXT"}</div>`;
 return "";
}
function sparkHTML(z,i,t,base){let a=HIST[z.label]||[],w=z.w,h=z.h;if(a.length<2)return `<div ${base}width:${w}px;height:${h}px;border-bottom:1px solid ${color(z.accent)}"></div>`;let max=z.auto?Math.max(...a,1):(z.max||100),min=z.auto?Math.min(...a,0):0,range=Math.max(1,max-min);let pts=a.map((v,n)=>`${(n/(a.length-1)*w).toFixed(1)},${(h-(v-min)/range*h).toFixed(1)}`).join(" ");return `<svg data-ei="${i}" style="${base.substring(base.indexOf("style=")+7)}width:${w}px;height:${h}px;overflow:visible" width="${w}" height="${h}"><polyline points="${pts}" fill="none" stroke="${color(z.accent)}" stroke-width="3"/><line x1="0" y1="${h-1}" x2="${w}" y2="${h-1}" stroke="#30343B"/></svg>`}
function dragElement(ev,i){if(imgEdit)return;ev.preventDefault();ei=i;let z=e(),sx=ev.clientX,sy=ev.clientY,ox=z.x,oy=z.y;function mv(a){z.x=Math.round(Math.max(0,Math.min(959,ox+(a.clientX-sx)/scale)));z.y=Math.round(Math.max(0,Math.min(375,oy+(a.clientY-sy)/scale)));renderCanvas();renderInspector()}function up(){removeEventListener("mousemove",mv);removeEventListener("mouseup",up)}addEventListener("mousemove",mv);addEventListener("mouseup",up)}
function renderSensors(){const x=$("sensors");if(!x)return;const q=(($("q")||{}).value||"").toLowerCase();x.innerHTML=S.filter(s=>(s.name+" "+s.id).toLowerCase().includes(q)).map(s=>`<div class="sensoritem addSensor" data-id="${s.id}" data-name="${s.name}"><b>${s.name}</b><br><span class="muted">${s.value}</span></div>`).join("");x.querySelectorAll(".addSensor").forEach(n=>n.onclick=()=>add({type:"sensor",label:n.dataset.id,title:n.dataset.name,x:80,y:90,size:24,unit:""}))}
function renderInspector(){const x=$("props");if(!x)return;if(ei<0){x.innerHTML=`<div class="tools"><button class="btn" id="addText">TEXT</button><button class="btn" id="addCard">LCARS CARD</button><button class="btn" id="addBar">BALKEN</button><button class="btn" id="addSpark">KURVE</button><button class="btn" id="addBadge">STATUS</button></div>`;bindAddButtons();return}let z=e();x.innerHTML=`<label>Typ<input value="${z.type}" disabled></label><label>Titel/Text<input id="et" value="${z.title??z.text??""}"></label><div class="row"><input id="ex" type="number" value="${z.x}"><input id="ey" type="number" value="${z.y}"></div><label>Akzent<select id="ea">${accents.map(a=>`<option>${a}</option>`).join("")}</select></label><div class="tools"><button class="btn" id="dup">DUPLIZIEREN</button><button class="btn" id="del">LÖSCHEN</button></div>`;$("ea").value=z.accent||"orange";["et","ex","ey","ea"].forEach(id=>$(id).onchange=applyInspector);$("dup").onclick=duplicate;$("del").onclick=del}
function bindAddButtons(){if($("addText"))$("addText").onclick=()=>add({type:"text",text:"TEXT",x:80,y:90,size:24});if($("addCard"))$("addCard").onclick=()=>add({type:"lcars_card",text:"GRUPPE",x:80,y:80,w:300,h:150,accent:"orange"});if($("addBar"))$("addBar").onclick=()=>add({type:"bar",label:"cpu_usage_percent",x:80,y:90,w:260,h:14,max:100,accent:"orange"});if($("addSpark"))$("addSpark").onclick=()=>add({type:"sparkline",label:"cpu_usage_percent",x:80,y:90,w:260,h:80,max:100,accent:"orange"});if($("addBadge"))$("addBadge").onclick=()=>add({type:"badge",label:"truenas_system_status",x:80,y:90,w:110,h:32})}
function applyInspector(){let z=e();if(z.type==="text"||z.type.startsWith("lcars_"))z.text=$("et").value;else z.title=$("et").value;z.x=+$("ex").value;z.y=+$("ey").value;z.accent=$("ea").value;renderCanvas()}
function add(z){p().elements??=[];p().elements.push(z);ei=p().elements.length-1;renderCanvas();renderInspector()}function duplicate(){let z=JSON.parse(JSON.stringify(e()));z.x+=14;z.y+=14;p().elements.push(z);ei=p().elements.length-1;renderCanvas();renderInspector()}function del(){p().elements.splice(ei,1);ei=-1;renderCanvas();renderInspector()}
function syncImageControls(){let im=p().image||={mode:"cover",x:0,y:0,zoom:1};if($("mode"))$("mode").value=im.mode;if($("zoom"))$("zoom").value=im.zoom;if($("ix"))$("ix").value=im.x;if($("iy"))$("iy").value=im.y}
function imageProp(){let im=p().image||={};im.mode=$("mode").value;im.zoom=+$("zoom").value;im.x=+$("ix").value;im.y=+$("iy").value;p().image=im;renderCanvas()}
function toggleImageEdit(){imgEdit=!imgEdit;$("imageEdit").textContent="BILDPOSITION: "+(imgEdit?"EIN":"AUS")}
$("canvas")?.addEventListener("mousedown",ev=>{if(!imgEdit)return;let im=p().image||={x:0,y:0},sx=ev.clientX,sy=ev.clientY,ox=im.x||0,oy=im.y||0;function mv(a){im.x=Math.round(ox+(a.clientX-sx)/scale);im.y=Math.round(oy+(a.clientY-sy)/scale);p().image=im;syncImageControls();renderCanvas()}function up(){removeEventListener("mousemove",mv);removeEventListener("mouseup",up)}addEventListener("mousemove",mv);addEventListener("mouseup",up)})
async function uploadImage(){let f=$("file").files[0];if(!f)return;let fd=new FormData();fd.append("image",f);let r=await fetch("/api/images",{method:"POST",body:fd}),j=await r.json();if(!r.ok){setStatus(j.error||"Upload fehlgeschlagen");return}p().background=j.file;await save();await renderImages();renderCanvas()}
async function renderImages(){let x=$("images")||$("imagelist");if(!x)return;let a=await jget("/api/images");x.innerHTML=a.map(v=>`<div class="sensoritem"><b>${v.name}</b><br>${v.width} × ${v.height}<br><button class="btn use" data-n="${v.name}">NUTZEN</button><button class="btn remove">VOM PANEL</button></div>`).join("");x.querySelectorAll(".use").forEach(b=>b.onclick=async()=>{p().background=b.dataset.n;await save();renderCanvas()});x.querySelectorAll(".remove").forEach(b=>b.onclick=async()=>{p().background="";await save();renderCanvas()})}
async function save(){await fetch("/api/layout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(L)});setStatus("Gespeichert.")}function setStatus(s){if($("status"))$("status").textContent=s}
init();setInterval(async()=>{try{V=await jget("/api/values");pushHistory();renderCanvas()}catch(e){}},5000);

/* v0.7.6 editor fixes */
function v076wire(){
 const rm=document.getElementById("removeImage")||Array.from(document.querySelectorAll("button")).find(b=>/BILD LÖSCHEN/i.test(b.textContent));
 if(rm)rm.onclick=async()=>{p().background="";await save();renderCanvas();setStatus("Bild vom Panel entfernt.");};
 const ie=document.getElementById("imageEdit");
 if(ie)ie.onclick=()=>{imgEdit=!imgEdit;ie.textContent="BILDPOSITION: "+(imgEdit?"EIN":"AUS");ie.classList.toggle("active",imgEdit);};
 ["mode","zoom","ix","iy"].forEach(id=>{const n=document.getElementById(id);if(n)n.onchange=()=>{imageProp();save();};});
 const stat=document.getElementById("status");
 if(stat){const b=document.createElement("div");b.innerHTML='<button class="btn" id="lcdPreview">LCD-VORSCHAU ERZEUGEN</button><button class="btn" id="lcdActivate">AUF LCD AKTIVIEREN</button><div id="histInfo" class="muted"></div>';stat.parentNode.appendChild(b);
 document.getElementById("lcdPreview").onclick=async()=>{await save();let r=await fetch("/api/lcd/generate",{method:"POST"}),j=await r.json();setStatus(j.ok?"LCD-Kandidat erzeugt: "+j.panels+" Panels":j.error);};
 document.getElementById("lcdActivate").onclick=async()=>{if(!confirm("Bestehende monitor.json sichern und generierte LCD-Konfiguration aktivieren?"))return;let r=await fetch("/api/lcd/activate",{method:"POST"}),j=await r.json();setStatus(j.ok?"monitor.json aktiviert. asterctl beim nächsten Neustart/Reload verwendet sie.":j.error);};}
}
const _oldPush=pushHistory;pushHistory=function(){_oldPush();const h=document.getElementById("histInfo");if(h){let n=(HIST["cpu_usage_percent"]||[]).length;h.textContent="VERLAUF: "+n+"/60 Messpunkte · ca. "+Math.round(n*5/60)+" Min.";}}
setTimeout(v076wire,0);

</script></body></html>"""

@app.get("/")
def index(): return Response(HTML,mimetype="text/html")
@app.get("/api/themes")
def themes(): return jsonify(THEMES)
@app.get("/api/values")
def api_values(): return jsonify(values())
@app.get("/api/sensors")
def api_sensors():
    v=values(); return jsonify([{"id":k,"name":friendly(k),"value":x} for k,x in sorted(v.items(),key=lambda z:friendly(z[0]).lower()) if "#unit" not in k])
@app.route("/api/layout",methods=["GET","POST"])
def layout():
    if request.method=="POST":
        LAYOUT.write_text(json.dumps(request.json,ensure_ascii=False,indent=2)); return jsonify(ok=True)
    return jsonify(load_layout())
@app.route("/api/images",methods=["GET","POST"])
def images():
    if request.method=="GET":
        out=[]
        for f in sorted(IMG.iterdir()):
            if f.suffix.lower() not in (".png",".jpg",".jpeg",".webp"): continue
            try:
                with Image.open(f) as im: w,h=im.size
                out.append({"name":f.name,"width":w,"height":h})
            except: pass
        return jsonify(out)
    f=request.files.get("image")
    if not f:return jsonify(ok=False,error="Keine Bilddatei ausgewählt."),400
    ext=Path(f.filename or "").suffix.lower()
    if ext not in (".png",".jpg",".jpeg",".webp"):return jsonify(ok=False,error="Erlaubt: PNG, JPG/JPEG, WebP."),400
    safe=re.sub(r"[^A-Za-z0-9._-]+","_",Path(f.filename).name)
    dst=IMG/safe; f.save(dst)
    try:
        with Image.open(dst) as im: im.verify()
    except:
        dst.unlink(missing_ok=True); return jsonify(ok=False,error="Ungültige Bilddatei."),400
    return jsonify(ok=True,file=safe)
@app.delete("/api/images/<path:name>")
def delete_image(name):
    f=(IMG/Path(name).name)
    if f.exists(): f.unlink()
    return jsonify(ok=True)
@app.get("/user-images/<path:name>")
def user_image(name): return send_from_directory(IMG,name)
@app.post("/api/prepare")
def prepare():
    stamp=time.strftime("%Y%m%d-%H%M%S")
    backup=""
    if MONITOR.exists():
        b=BACKUP/f"monitor-{stamp}.json"; shutil.copy2(MONITOR,b); backup=b.name
    candidate=CFG/"monitor-v07-candidate.json"
    candidate.write_text(json.dumps(load_layout(),ensure_ascii=False,indent=2))
    return jsonify(ok=True,message=f"Backup: {backup or 'nicht vorhanden'} · Kandidat: {candidate.name}. Noch keine automatische Umschaltung.")

@app.post("/api/lcd/generate")
def lcd_generate():
    import subprocess, json
    try:
        r=subprocess.run(["python3","/app/lcd_generator.py"],capture_output=True,text=True,timeout=20)
        if r.returncode != 0: return jsonify(ok=False,error=r.stderr or r.stdout),500
        return jsonify(json.loads(r.stdout.strip().splitlines()[-1]))
    except Exception as e: return jsonify(ok=False,error=str(e)),500

@app.post("/api/lcd/activate")
def lcd_activate():
    import subprocess, json
    try:
        r=subprocess.run(["python3","/app/lcd_generator.py","--activate"],capture_output=True,text=True,timeout=20)
        if r.returncode != 0: return jsonify(ok=False,error=r.stderr or r.stdout),500
        return jsonify(json.loads(r.stdout.strip().splitlines()[-1]))
    except Exception as e: return jsonify(ok=False,error=str(e)),500
if __name__=="__main__":
    app.run(host="0.0.0.0",port=8765)
