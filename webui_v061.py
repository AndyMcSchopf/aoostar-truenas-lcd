#!/usr/bin/env python3
from flask import Flask,jsonify,request,send_from_directory,Response
from pathlib import Path
from PIL import Image
import json,os,re,shutil,time
app=Flask(__name__)
CFG=Path(os.environ.get("AOOSTAR_CFG","/app/cfg")); SENS=CFG/"sensors"/"values.txt"; IMG=CFG/"images"; IMG.mkdir(parents=True,exist_ok=True)
LAYOUT=CFG/"layout-v061.json"; MON=CFG/"monitor.json"
W,H=960,376
DEFAULT={"version":"0.6.1","canvas":{"width":W,"height":H},"panels":[
{"name":"SYSTEM","duration":6,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},"elements":[
{"type":"box","x":28,"y":58,"w":275,"h":190,"title":"CPU","radius":16},
{"type":"sensor","label":"cpu_usage_percent","title":"Auslastung","x":55,"y":105,"size":38,"unit":"%"},
{"type":"sensor","label":"temperature_cpu","title":"Temperatur","x":55,"y":170,"size":28,"unit":"°C"},
{"type":"bar","label":"cpu_usage_percent","x":55,"y":218,"w":220,"h":14,"max":100},
{"type":"box","x":326,"y":58,"w":275,"h":190,"title":"RAM","radius":16},
{"type":"sensor","label":"mem_usage_percent","title":"Belegung","x":353,"y":105,"size":38,"unit":"%"},
{"type":"sensor","label":"temperature_memory","title":"Temperatur","x":353,"y":170,"size":28,"unit":"°C"},
{"type":"bar","label":"mem_usage_percent","x":353,"y":218,"w":220,"h":14,"max":100},
{"type":"box","x":624,"y":58,"w":308,"h":190,"title":"NETZWERK","radius":16},
{"type":"sensor","label":"truenas_net_down","title":"Download","x":650,"y":108,"size":26,"unit":""},
{"type":"sensor","label":"truenas_net_up","title":"Upload","x":650,"y":168,"size":26,"unit":""},
{"type":"text","text":"TrueSTARMax","x":28,"y":20,"size":26},{"type":"badge","label":"truenas_system_status","x":830,"y":18,"w":100,"h":30}]},
{"name":"SPEICHER / ZFS","duration":7,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},"elements":[]},
{"name":"TRUENAS","duration":7,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},"elements":[]},
{"name":"BILD","duration":10,"background":"","image":{"mode":"cover","x":0,"y":0,"zoom":1.0},"elements":[
{"type":"box","x":20,"y":310,"w":920,"h":50,"title":"","radius":14},
{"type":"sensor","label":"truenas_system_status","title":"TrueSTARMax","x":42,"y":325,"size":20,"unit":""},
{"type":"sensor","label":"cpu_usage_percent","title":"CPU","x":690,"y":325,"size":20,"unit":"%"},
{"type":"sensor","label":"temperature_cpu","title":"","x":825,"y":325,"size":20,"unit":"°C"}]}]}
ALIASES={"cpu_usage_percent":"CPU – Auslastung","temperature_cpu":"CPU – Temperatur","mem_usage_percent":"RAM – Belegung","temperature_memory":"RAM – Temperatur","temperature_gpu":"GPU – Temperatur","truenas_net_down":"LAN – Download","truenas_net_up":"LAN – Upload","truenas_version":"TrueNAS – Version","truenas_system_status":"TrueNAS – Systemstatus","truenas_apps_running":"Apps – aktiv","truenas_apps_stopped":"Apps – gestoppt","truenas_apps_crashed":"Apps – fehlerhaft","truenas_apps_updates":"Apps – Updates","truenas_pools_healthy":"ZFS – gesunde Pools"}
def vals():
 o={}
 if SENS.exists():
  for l in SENS.read_text(errors="replace").splitlines():
   if ":" in l:
    k,v=l.split(":",1);o[k.strip()]=v.strip()
 return o
def friendly(k):
 if k in ALIASES:return ALIASES[k]
 m=re.match(r"truenas_pool_(\d+)_(.+)",k)
 if m:
  q={"name":"Name","status":"Status","healthy":"Gesund","used_percent":"Belegung","used":"Belegt","free":"Frei","size":"Größe","scan":"Scrub"}
  return f"ZFS Pool {int(m.group(1))+1} – {q.get(m.group(2),m.group(2))}"
 if k.startswith("temperature_nvme_"):return "NVMe – "+k.split("_",3)[-1].replace("_"," ")+" – Temperatur"
 if k.startswith("temperature_drivetemp_"):return "HDD – "+k[len("temperature_drivetemp_"):].replace("_"," ")+" – Temperatur"
 return k
def load_layout():
 if not LAYOUT.exists():LAYOUT.write_text(json.dumps(DEFAULT,ensure_ascii=False,indent=2))
 try:return json.loads(LAYOUT.read_text())
 except:return DEFAULT

HTML=r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AOOSTAR TrueNAS LCD</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e5e7eb;font:14px Arial}header{padding:14px 20px;background:#111827;border-bottom:1px solid #334155}
main{display:grid;grid-template-columns:285px minmax(500px,1fr) 285px;gap:12px;padding:12px}.card{background:#162033;border:1px solid #334155;border-radius:10px;padding:11px;margin-bottom:10px}
.btn{background:#243247;color:#fff;border:1px solid #475569;border-radius:6px;padding:7px 9px;margin:2px;cursor:pointer}.active{outline:2px solid #cbd5e1}
.viewport{width:100%;overflow:hidden}.canvas{position:relative;width:960px;height:376px;background:#020617;transform-origin:top left;overflow:hidden;border:1px solid #64748b}
.el{position:absolute;cursor:move;user-select:none}.sel{outline:2px dashed #fff}.boxel{border:1px solid #475569;background:#111827bb}.boxtitle{position:absolute;top:10px;left:14px;color:#94a3b8;font-size:15px}.barbg{background:#334155;border-radius:8px;overflow:hidden}.barfill{height:100%;background:#cbd5e1}
.badge{border:1px solid #64748b;border-radius:18px;background:#172033;display:flex;align-items:center;justify-content:center}.label{font-size:.55em;color:#94a3b8;display:block}
input,select{width:100%;background:#0f172a;color:#fff;border:1px solid #475569;border-radius:5px;padding:6px;margin:3px 0}.row{display:flex;gap:5px}.row>*{flex:1}.sensor{padding:6px;border-bottom:1px solid #334155;cursor:pointer}.muted{color:#94a3b8}.toolrow{display:flex;flex-wrap:wrap}
@media(max-width:1100px){main{grid-template-columns:1fr}.canvas{transform:scale(.75);margin-bottom:-94px}}
</style></head><body><header><b>AOOSTAR TrueNAS LCD – Panel-Editor v0.6.1</b> <span class="muted">· native 960 × 376</span></header><main>
<div><div class="card"><b>Panels</b><div id="panels"></div><button class="btn" onclick="addPanel()">+ Panel</button></div>
<div class="card"><b>Elemente</b><div class="toolrow"><button class="btn" onclick="addText()">Text</button><button class="btn" onclick="addBox()">Gruppe/Box</button><button class="btn" onclick="addLine()">Linie</button><button class="btn" onclick="addBar()">Balken</button><button class="btn" onclick="addBadge()">Status-Badge</button></div></div>
<div class="card"><b>Sensoren</b><input id="q" placeholder="Sensor suchen…" oninput="renderSensors()"><div id="sensors" style="max-height:300px;overflow:auto"></div></div></div>
<div><div class="card"><div class="row"><input id="pname" onchange="panelProp()"><input id="pdur" type="number" min="1" onchange="panelProp()"></div>
<div class="viewport" id="vp"><div class="canvas" id="canvas"></div></div>
<div class="toolrow"><button class="btn" onclick="save()">Speichern</button><button class="btn" onclick="file.click()">Bild hochladen</button><input id="file" type="file" accept="image/*" hidden onchange="upload()"><button class="btn" id="imgedit" onclick="toggleImageEdit()">Bildposition bearbeiten: AUS</button></div>
<div class="row"><select id="mode" onchange="imageProp()"><option value="contain">Einpassen</option><option value="cover">Ausfüllen/Zuschneiden</option><option value="center">Originalgröße</option></select><input id="zoom" type="number" min=".25" max="4" step=".05" onchange="imageProp()" title="Zoom"><input id="ix" type="number" onchange="imageProp()" title="Bild X"><input id="iy" type="number" onchange="imageProp()" title="Bild Y"></div>
<div class="toolrow"><button class="btn" onclick="alignImg('center')">Bild zentrieren</button><button class="btn" onclick="alignImg('left')">Links</button><button class="btn" onclick="alignImg('right')">Rechts</button><button class="btn" onclick="resetImg()">Bild zurücksetzen</button></div></div></div>
<div><div class="card"><b>Eigenschaften</b><div id="props" class="muted">Element auswählen.</div></div><div class="card"><b>LCD</b><button class="btn" onclick="prepare()">Auf LCD vorbereiten</button><div id="status" class="muted"></div></div></div>
</main><script>
let L={},V={},S=[],pi=0,ei=-1,imgEdit=false,scale=1;
async function init(){L=await(await fetch('/api/layout')).json();V=await(await fetch('/api/values')).json();S=await(await fetch('/api/sensors')).json();render();addEventListener('resize',fit)}
function fit(){scale=Math.min(1,vp.clientWidth/960);canvas.style.transform=`scale(${scale})`;vp.style.height=(376*scale)+'px'}
function render(){renderPanels();renderCanvas();renderSensors();fit()}
function p(){return L.panels[pi]} function e(){return p().elements[ei]}
function renderPanels(){panels.innerHTML=L.panels.map((x,i)=>`<button class="btn ${i==pi?'active':''}" onclick="pi=${i};ei=-1;render()">${i+1} ${x.name}</button>`).join('');pname.value=p().name;pdur.value=p().duration;let im=p().image||={mode:'cover',x:0,y:0,zoom:1};mode.value=im.mode;zoom.value=im.zoom;ix.value=im.x;iy.value=im.y}
function bg(){let x=p(),im=x.image||{};if(!x.background)return 'none';return `url('/user-images/${x.background}')`}
function renderCanvas(){let x=p(),im=x.image||{};canvas.style.backgroundImage=bg();canvas.style.backgroundRepeat='no-repeat';canvas.style.backgroundPosition=`${im.x||0}px ${im.y||0}px`;canvas.style.backgroundSize=im.mode==='contain'?'contain':im.mode==='cover'?`${(im.zoom||1)*100}% auto`: 'auto';canvas.innerHTML=x.elements.map((z,i)=>htmlEl(z,i)).join('');propsUI()}
function htmlEl(z,i){let c=`el ${i==ei?'sel':''}`,common=`class="${c}" onmousedown="drag(event,${i})" onclick="sel(event,${i})"`;
if(z.type==='box')return `<div ${common} style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px;border-radius:${z.radius||0}px" class="${c} boxel"><span class=boxtitle>${z.title||''}</span></div>`;
if(z.type==='line')return `<div ${common} style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h||2}px;background:#64748b"></div>`;
if(z.type==='bar'){let n=parseFloat(V[z.label]||0),pct=Math.max(0,Math.min(100,n/(z.max||100)*100));return `<div ${common} style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px" class="${c} barbg"><div class=barfill style="width:${pct}%"></div></div>`}
if(z.type==='badge')return `<div ${common} style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px" class="${c} badge">${V[z.label]??'–'}</div>`;
if(z.type==='text')return `<div ${common} style="left:${z.x}px;top:${z.y}px;font-size:${z.size}px">${z.text||'Text'}</div>`;
return `<div ${common} style="left:${z.x}px;top:${z.y}px;font-size:${z.size}px"><span class=label>${z.title||''}</span>${V[z.label]??'–'} ${z.unit||''}</div>`}
function sel(ev,i){ev.stopPropagation();ei=i;renderCanvas()}
function drag(ev,i){if(imgEdit)return;ei=i;let z=e(),sx=ev.clientX,sy=ev.clientY,ox=z.x,oy=z.y;function mv(a){z.x=Math.round(Math.max(0,Math.min(959,ox+(a.clientX-sx)/scale)));z.y=Math.round(Math.max(0,Math.min(375,oy+(a.clientY-sy)/scale)));renderCanvas()}function up(){removeEventListener('mousemove',mv);removeEventListener('mouseup',up)}addEventListener('mousemove',mv);addEventListener('mouseup',up)}
canvas.addEventListener('mousedown',ev=>{if(!imgEdit)return;let im=p().image,sx=ev.clientX,sy=ev.clientY,ox=im.x||0,oy=im.y||0;function mv(a){im.x=Math.round(ox+(a.clientX-sx)/scale);im.y=Math.round(oy+(a.clientY-sy)/scale);ix.value=im.x;iy.value=im.y;renderCanvas()}function up(){removeEventListener('mousemove',mv);removeEventListener('mouseup',up)}addEventListener('mousemove',mv);addEventListener('mouseup',up)})
function propsUI(){if(ei<0){props.innerHTML='Element auswählen.';return}let z=e();props.innerHTML=`<label>Typ<input value="${z.type}" disabled></label><label>Titel/Text<input id=pt value="${z.title??z.text??''}" onchange=prop()></label><div class=row><input id=px type=number value="${z.x}" onchange=prop()><input id=py type=number value="${z.y}" onchange=prop()></div><div class=row><input id=pw type=number value="${z.w||0}" onchange=prop()><input id=ph type=number value="${z.h||0}" onchange=prop()></div><label>Schriftgröße<input id=ps type=number value="${z.size||24}" onchange=prop()></label><button class=btn onclick=delEl()>Löschen</button>`}
function prop(){let z=e();if(z.type==='text')z.text=pt.value;else z.title=pt.value;z.x=+px.value;z.y=+py.value;if(z.w!==undefined)z.w=+pw.value;if(z.h!==undefined)z.h=+ph.value;if(z.size!==undefined)z.size=+ps.value;renderCanvas()}
function add(o){p().elements.push(o);ei=p().elements.length-1;renderCanvas()} function addText(){add({type:'text',text:'Überschrift',x:50,y:30,size:28})} function addBox(){add({type:'box',title:'GRUPPE',x:50,y:60,w:300,h:180,radius:16})} function addLine(){add({type:'line',x:50,y:100,w:300,h:2})} function addBar(){add({type:'bar',label:'cpu_usage_percent',x:50,y:100,w:250,h:14,max:100})} function addBadge(){add({type:'badge',label:'truenas_system_status',x:50,y:50,w:110,h:32})}
function addSensor(id,n){add({type:'sensor',label:id,title:n,x:60,y:60,size:24,unit:''})} function delEl(){p().elements.splice(ei,1);ei=-1;renderCanvas()}
function renderSensors(){let t=(q.value||'').toLowerCase();sensors.innerHTML=S.filter(x=>(x.name+' '+x.id).toLowerCase().includes(t)).map(x=>`<div class=sensor onclick='addSensor(${JSON.stringify(x.id)},${JSON.stringify(x.name)})'><b>${x.name}</b><br><span class=muted>${x.value}</span></div>`).join('')}
function panelProp(){p().name=pname.value;p().duration=+pdur.value;renderPanels()} function addPanel(){L.panels.push({name:'NEUES PANEL',duration:6,background:'',image:{mode:'cover',x:0,y:0,zoom:1},elements:[]});pi=L.panels.length-1;ei=-1;render()}
function imageProp(){let im=p().image;im.mode=mode.value;im.zoom=+zoom.value;im.x=+ix.value;im.y=+iy.value;renderCanvas()} function resetImg(){p().image={mode:'cover',x:0,y:0,zoom:1};renderPanels();renderCanvas()} function alignImg(a){let im=p().image;if(a==='center'){im.x=0;im.y=0}else if(a==='left')im.x=0;else if(a==='right')im.x=0;renderPanels();renderCanvas()}
function toggleImageEdit(){imgEdit=!imgEdit;imgedit.textContent='Bildposition bearbeiten: '+(imgEdit?'EIN':'AUS');imgedit.classList.toggle('active',imgEdit)}
async function upload(){let f=file.files[0];if(!f)return;let fd=new FormData();fd.append('image',f);let j=await(await fetch('/api/image',{method:'POST',body:fd})).json();if(j.ok){p().background=j.file;resetImg();await save()}}
async function save(){await fetch('/api/layout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(L)});status.textContent='Gespeichert.'}
async function prepare(){await save();let j=await(await fetch('/api/activate',{method:'POST'})).json();status.textContent=j.message||j.error}
init();setInterval(async()=>{V=await(await fetch('/api/values')).json();renderCanvas()},5000)
</script></body></html>"""

@app.get("/")
def index():return Response(HTML,mimetype="text/html")
@app.get("/api/values")
def av():return jsonify(vals())
@app.get("/api/sensors")
def sensors():
 v=vals();return jsonify([{"id":k,"name":friendly(k),"value":x} for k,x in sorted(v.items(),key=lambda z:friendly(z[0]).lower()) if "#unit" not in k])
@app.route("/api/layout",methods=["GET","POST"])
def layout():
 if request.method=="POST":LAYOUT.write_text(json.dumps(request.json,ensure_ascii=False,indent=2));return jsonify(ok=True)
 return jsonify(load_layout())
@app.post("/api/image")
def image():
 f=request.files.get("image")
 if not f:return jsonify(ok=False,error="Keine Datei."),400
 ext=Path(f.filename or "").suffix.lower()
 if ext not in (".png",".jpg",".jpeg",".webp"):return jsonify(ok=False,error="PNG, JPG oder WebP erforderlich."),400
 name=f"panel_{int(time.time())}{ext}";dst=IMG/name;f.save(dst)
 try:
  with Image.open(dst) as im:im.verify()
 except:dst.unlink(missing_ok=True);return jsonify(ok=False,error="Ungültiges Bild."),400
 return jsonify(ok=True,file=name)
@app.get("/user-images/<path:n>")
def user_image(n):return send_from_directory(IMG,n)
@app.post("/api/activate")
def activate():
 backup=""
 if MON.exists():
  b=CFG/f"monitor.backup-{int(time.time())}.json";shutil.copy2(MON,b);backup=b.name
 c=CFG/"monitor-v061-candidate.json";c.write_text(json.dumps(load_layout(),ensure_ascii=False,indent=2))
 return jsonify(ok=True,message=f"Backup: {backup or 'nicht vorhanden'}; Kandidat: {c.name}. Noch keine automatische Umschaltung.")
if __name__=="__main__":app.run(host="0.0.0.0",port=8765)
