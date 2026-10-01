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
let L={},V={},S=[],T={},pi=0,ei=-1,imgEdit=false,scale=1;
const A={orange:'#F29A49',amber:'#F6B85A',violet:'#8E7CC3',blue:'#6699CC',pink:'#C96B9A'};
async function init(){L=await(await fetch('/api/layout')).json();V=await(await fetch('/api/values')).json();S=await(await fetch('/api/sensors')).json();T=await(await fetch('/api/themes')).json();theme.innerHTML=Object.entries(T).map(([k,v])=>`<option value="${k}">${v.name}</option>`).join('');render();loadImages();addEventListener('resize',fit)}
function fit(){scale=Math.min(1,vp.clientWidth/960);canvas.style.transform=`scale(${scale})`;vp.style.height=(376*scale)+'px'}function p(){return L.panels[pi]}function e(){return p().elements[ei]}function col(z){let th=T[L.theme]||T['lcars-orange'];return th[z.accent]||th.orange}
function render(){renderPanels();renderCanvas();renderSensors();theme.value=L.theme;fit()}
function renderPanels(){panels.innerHTML=L.panels.map((x,i)=>`<button class="btn ${i==pi?'active':''}" onclick="pi=${i};ei=-1;render()">${i+1} ${x.name}</button>`).join('');pname.value=p().name;pdur.value=p().duration;let im=p().image||={mode:'cover',x:0,y:0,zoom:1};mode.value=im.mode;zoom.value=im.zoom;ix.value=im.x;iy.value=im.y}
function renderCanvas(){let x=p(),im=x.image||{},th=T[L.theme]||T['lcars-orange'];canvas.style.background=th.bg;canvas.style.backgroundImage=x.background?`url('/user-images/${x.background}')`:'none';canvas.style.backgroundRepeat='no-repeat';canvas.style.backgroundPosition=`${im.x||0}px ${im.y||0}px`;canvas.style.backgroundSize=im.mode==='contain'?'contain':im.mode==='cover'?`${(im.zoom||1)*100}% auto`:'auto';canvas.innerHTML=x.elements.map((z,i)=>html(z,i,th)).join('');propsUI()}
function html(z,i,th){let c=`el ${i==ei?'sel':''}`,common=`class="${c}" onmousedown="drag(event,${i})" onclick="sel(event,${i})"`,ac=col(z);
if(z.type==='lcars_header'||z.type==='lcars_footer')return `<div ${common} class="${c} ${z.type==='lcars_header'?'lcars-header':'lcars-footer'}" style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px;background:${ac}">${z.text}</div>`;
if(z.type==='lcars_elbow')return `<div ${common} class="${c} lcars-elbow" style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px;background:${ac}">${z.text}</div>`;
if(z.type==='lcars_card')return `<div ${common} class="${c} lcars-card" style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px"><div class=cap style="background:${ac}">${z.text}</div></div>`;
if(z.type==='pool'){let n=z.index,k='truenas_pool_'+n+'_',pct=parseFloat(V[k+'used_percent']||0);return `<div ${common} class="${c} pool" style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px"><div class=head style="background:${ac}">${V[k+'name']||'POOL '+(n+1)} · ${V[k+'status']||''}</div><div class=body><span class=pct>${V[k+'used_percent']||'–'} %</span> <span class=small>${V[k+'used']||''} / ${V[k+'size']||''}</span><div class=bar style="height:11px;margin-top:10px"><div style="height:100%;width:${pct}%;background:${ac}"></div></div></div></div>`;
if(z.type==='bar'){let n=parseFloat(V[z.label]||0),pct=Math.max(0,Math.min(100,n/(z.max||100)*100));return `<div ${common} class="${c} bar" style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px"><div style="height:100%;width:${pct}%;background:${ac}"></div></div>`}
if(z.type==='badge')return `<div ${common} class="${c} badge" style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px">${V[z.label]??'–'}</div>`;
if(z.type==='text')return `<div ${common} style="left:${z.x}px;top:${z.y}px;font-size:${z.size}px;color:${th.text}">${z.text}</div>`;
return `<div ${common} style="left:${z.x}px;top:${z.y}px;font-size:${z.size}px;color:${th.text}"><span class=sensor-label>${z.title||''}</span>${V[z.label]??'–'} ${z.unit||''}</div>`}
function sel(ev,i){ev.stopPropagation();ei=i;renderCanvas()}function drag(ev,i){if(imgEdit)return;ei=i;let z=e(),sx=ev.clientX,sy=ev.clientY,ox=z.x,oy=z.y;function mv(a){z.x=Math.round(Math.max(0,Math.min(959,ox+(a.clientX-sx)/scale)));z.y=Math.round(Math.max(0,Math.min(375,oy+(a.clientY-sy)/scale)));renderCanvas()}function up(){removeEventListener('mousemove',mv);removeEventListener('mouseup',up)}addEventListener('mousemove',mv);addEventListener('mouseup',up)}
canvas.addEventListener('mousedown',ev=>{if(!imgEdit)return;let im=p().image,sx=ev.clientX,sy=ev.clientY,ox=im.x||0,oy=im.y||0;function mv(a){im.x=Math.round(ox+(a.clientX-sx)/scale);im.y=Math.round(oy+(a.clientY-sy)/scale);ix.value=im.x;iy.value=im.y;renderCanvas()}function up(){removeEventListener('mousemove',mv);removeEventListener('mouseup',up)}addEventListener('mousemove',mv);addEventListener('mouseup',up)})
function propsUI(){if(ei<0){props.innerHTML='Element auswählen.';return}let z=e();props.innerHTML=`<label>Typ<input value="${z.type}" disabled></label><label>Titel/Text<input id=pt value="${z.title??z.text??''}" onchange=prop()></label><div class=row><input id=px type=number value="${z.x}" onchange=prop()><input id=py type=number value="${z.y}" onchange=prop()></div><label>Akzent<select id=pa onchange=prop()><option>orange</option><option>amber</option><option>violet</option><option>blue</option><option>pink</option></select></label><button class=btn onclick=dup()>DUPLIZIEREN</button><button class=btn onclick=delEl()>LÖSCHEN</button>`;if(z.accent)pa.value=z.accent}
function prop(){let z=e();if(z.type==='text'||z.type.startsWith('lcars_'))z.text=pt.value;else z.title=pt.value;z.x=+px.value;z.y=+py.value;z.accent=pa.value;renderCanvas()}function dup(){let z=JSON.parse(JSON.stringify(e()));z.x+=12;z.y+=12;p().elements.push(z);ei=p().elements.length-1;renderCanvas()}function delEl(){p().elements.splice(ei,1);ei=-1;renderCanvas()}
function add(o){p().elements.push(o);ei=p().elements.length-1;renderCanvas()}function addText(){add({type:'text',text:'TEXT',x:80,y:80,size:24})}function addCard(){add({type:'lcars_card',text:'GRUPPE',x:80,y:80,w:300,h:150,accent:'orange'})}function addBadge(){add({type:'badge',label:'truenas_system_status',x:80,y:80,w:110,h:32})}function addBar(){add({type:'bar',label:'cpu_usage_percent',x:80,y:80,w:260,h:14,max:100,accent:'orange'})}function addSensor(id,n){add({type:'sensor',label:id,title:n,x:80,y:80,size:24,unit:''})}
function renderSensors(){let t=(q.value||'').toLowerCase();sensors.innerHTML=S.filter(x=>(x.name+' '+x.id).toLowerCase().includes(t)).map(x=>`<div class=sensoritem onclick='addSensor(${JSON.stringify(x.id)},${JSON.stringify(x.name)})'><b>${x.name}</b><br><span class=muted>${x.value}</span></div>`).join('')}
function panelProp(){p().name=pname.value;p().duration=+pdur.value;renderPanels()}function themeProp(){L.theme=theme.value;renderCanvas()}function addPanel(){L.panels.push({name:'NEUES PANEL',duration:6,background:'',image:{mode:'cover',x:0,y:0,zoom:1},elements:[]});pi=L.panels.length-1;ei=-1;render()}
function imageProp(){let im=p().image;im.mode=mode.value;im.zoom=+zoom.value;im.x=+ix.value;im.y=+iy.value;renderCanvas()}function toggleImageEdit(){imgEdit=!imgEdit;imgedit.textContent='BILDPOSITION: '+(imgEdit?'EIN':'AUS');imgedit.classList.toggle('active',imgEdit)}
async function upload(){let f=file.files[0];if(!f)return;let fd=new FormData();fd.append('image',f);let j=await(await fetch('/api/images',{method:'POST',body:fd})).json();if(j.ok){p().background=j.file;await save();renderCanvas();loadImages()}else alert(j.error)}
async function removeImage(){p().background='';await save();renderCanvas()}async function loadImages(){let a=await(await fetch('/api/images')).json();imagelist.innerHTML=a.map(x=>`<div class=sensoritem><b>${x.name}</b><br>${x.width}×${x.height} <button class=btn onclick="useImage('${x.name}')">NUTZEN</button> <button class=btn onclick="deleteImage('${x.name}')">LÖSCHEN</button></div>`).join('')}function useImage(n){p().background=n;save();renderCanvas()}async function deleteImage(n){await fetch('/api/images/'+encodeURIComponent(n),{method:'DELETE'});if(p().background===n)p().background='';await save();loadImages();renderCanvas()}
async function save(){await fetch('/api/layout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(L)});status.textContent='GESPEICHERT'}async function prepare(){await save();let j=await(await fetch('/api/prepare',{method:'POST'})).json();status.textContent=j.message||j.error}
init();setInterval(async()=>{V=await(await fetch('/api/values')).json();renderCanvas()},5000)
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
if __name__=="__main__":
    app.run(host="0.0.0.0",port=8765)
