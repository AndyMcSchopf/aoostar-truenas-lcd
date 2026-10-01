#!/usr/bin/env python3
from flask import Flask,jsonify,request,send_from_directory,Response
from pathlib import Path
from PIL import Image
import json,os,re,shutil,time
app=Flask(__name__)
CFG=Path(os.environ.get("AOOSTAR_CFG","/app/cfg"));SENS=CFG/"sensors"/"values.txt";IMG=CFG/"images";IMG.mkdir(parents=True,exist_ok=True);LAYOUT=CFG/"layout-v06.json";MON=CFG/"monitor.json"
DEFAULT={"version":"0.6.0","panels":[
{"name":"SYSTEM","duration":6,"background":"","mode":"contain","elements":[{"label":"cpu_usage_percent","title":"CPU","x":45,"y":80,"size":34,"unit":"%"},{"label":"temperature_cpu","title":"CPU Temp.","x":45,"y":140,"size":28,"unit":"C"},{"label":"mem_usage_percent","title":"RAM","x":400,"y":80,"size":34,"unit":"%"},{"label":"temperature_gpu","title":"GPU","x":400,"y":140,"size":28,"unit":"C"},{"label":"truenas_net_down","title":"Download","x":45,"y":300,"size":24,"unit":""},{"label":"truenas_net_up","title":"Upload","x":400,"y":300,"size":24,"unit":""}]},
{"name":"SPEICHER / ZFS","duration":7,"background":"","mode":"contain","elements":[{"label":"truenas_pools_healthy","title":"Pools","x":45,"y":65,"size":30,"unit":""},{"label":"truenas_pool_0_used_percent","title":"NVME 2TB #1","x":45,"y":125,"size":26,"unit":"%"},{"label":"truenas_pool_1_used_percent","title":"NVME 2TB #2","x":45,"y":180,"size":26,"unit":"%"},{"label":"truenas_pool_2_used_percent","title":"NVME 4TB","x":400,"y":125,"size":26,"unit":"%"},{"label":"truenas_pool_3_used_percent","title":"18TB Z1","x":400,"y":180,"size":26,"unit":"%"}]},
{"name":"TRUENAS","duration":7,"background":"","mode":"contain","elements":[{"label":"truenas_version","title":"Version","x":45,"y":70,"size":26,"unit":""},{"label":"truenas_system_status","title":"System","x":45,"y":125,"size":30,"unit":""},{"label":"truenas_apps_running","title":"Apps aktiv","x":45,"y":180,"size":28,"unit":""},{"label":"truenas_apps_updates","title":"Updates","x":400,"y":125,"size":28,"unit":""},{"label":"truenas_apps_crashed","title":"Fehler","x":400,"y":180,"size":28,"unit":""}]},
{"name":"BILD","duration":10,"background":"","mode":"contain","elements":[]}]}
ALIASES={"cpu_usage_percent":"CPU - Auslastung","temperature_cpu":"CPU - Temperatur","mem_usage_percent":"RAM - Belegung","temperature_memory":"RAM - Temperatur","temperature_gpu":"GPU - Temperatur","truenas_net_down":"LAN - Download","truenas_net_up":"LAN - Upload","truenas_version":"TrueNAS - Version","truenas_system_status":"TrueNAS - Systemstatus","truenas_apps_running":"Apps - aktiv","truenas_apps_stopped":"Apps - gestoppt","truenas_apps_crashed":"Apps - fehlerhaft","truenas_apps_updates":"Apps - Updates","truenas_pools_healthy":"ZFS - gesunde Pools"}
def load_layout():
 if not LAYOUT.exists():LAYOUT.write_text(json.dumps(DEFAULT,ensure_ascii=False,indent=2))
 try:return json.loads(LAYOUT.read_text())
 except:return DEFAULT
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
  n=int(m.group(1))+1;q={"name":"Name","status":"Status","healthy":"Gesund","used_percent":"Belegung","used":"Belegt","free":"Frei","size":"Groesse","scan":"Scrub"}
  return f"ZFS Pool {n} - {q.get(m.group(2),m.group(2))}"
 if k.startswith("temperature_nvme_"):return "NVMe - "+k.split("_",3)[-1].replace("_"," ")+" - Temperatur"
 if k.startswith("temperature_drivetemp_"):return "HDD - "+k[len("temperature_drivetemp_"):].replace("_"," ")+" - Temperatur"
 return k
HTML='<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AOOSTAR TrueNAS LCD</title>\n<style>*{box-sizing:border-box}body{margin:0;background:#0f172a;color:#e5e7eb;font:14px Arial}header{padding:15px 22px;background:#111827;border-bottom:1px solid #334155}main{display:grid;grid-template-columns:310px 1fr 330px;gap:14px;padding:14px}.box{background:#182235;border:1px solid #334155;border-radius:9px;padding:12px}.btn{background:#243247;color:white;border:1px solid #475569;border-radius:6px;padding:8px;margin:2px;cursor:pointer}.active{outline:2px solid #94a3b8}.preview{position:relative;width:min(800px,100%);aspect-ratio:16/9;background:#030712;border:1px solid #64748b;overflow:hidden;background-repeat:no-repeat;background-position:center}.el{position:absolute;padding:4px 7px;border:1px dashed transparent;cursor:move;white-space:nowrap}.el.sel{border-color:#f8fafc;background:#1e293b99}.title{font-size:.55em;color:#cbd5e1;display:block}.sensor{padding:7px;border-bottom:1px solid #334155;cursor:pointer}.muted{color:#94a3b8}input,select{width:100%;padding:7px;margin:4px 0;background:#0f172a;color:white;border:1px solid #475569;border-radius:5px}.row{display:flex;gap:5px}.row>*{flex:1}@media(max-width:1050px){main{grid-template-columns:1fr}.preview{width:100%}}</style></head>\n<body><header><b>AOOSTAR TrueNAS LCD - Visueller Panel-Editor v0.6</b> <span class="muted">- 800 x 450 Arbeitsflaeche</span></header><main>\n<div><div class="box"><b>Panels</b><div id="panels"></div><button class="btn" onclick="addPanel()">+ Panel</button></div><div class="box"><b>Sensoren</b><input id="q" placeholder="Sensor suchen..." oninput="renderSensors()"><div id="sensors" style="max-height:430px;overflow:auto"></div></div></div>\n<div><div class="box"><div class="row"><input id="pname" onchange="panelProp()"><input id="pdur" type="number" min="1" onchange="panelProp()"></div><div class="preview" id="preview"></div><div><button class="btn" onclick="save()">Speichern</button><button class="btn" onclick="file.click()">Bild hochladen</button><input id="file" type="file" accept="image/*" hidden onchange="upload()"><select id="mode" onchange="panelProp()"><option value="contain">Bild einpassen</option><option value="cover">Bild ausfuellen</option><option value="center">Zentrieren</option></select></div></div></div>\n<div><div class="box"><b>Element</b><div id="props" class="muted">Element anklicken oder Sensor hinzufuegen.</div></div><div class="box"><b>LCD</b><p class="muted">Aktivierung erstellt zuerst ein Backup.</p><button class="btn" onclick="activate()">Auf LCD vorbereiten</button><div id="status" class="muted"></div></div></div>\n</main><script>\nlet L={},V={},S=[],pi=0,ei=-1;\nasync function init(){L=await(await fetch(\'/api/layout\')).json();V=await(await fetch(\'/api/values\')).json();S=await(await fetch(\'/api/sensors\')).json();render()}\nfunction render(){renderPanels();renderPreview();renderSensors()}\nfunction renderPanels(){panels.innerHTML=L.panels.map((p,i)=>`<button class="btn ${i==pi?\'active\':\'\'}" onclick="pi=${i};ei=-1;render()">${i+1} ${p.name}</button>`).join(\'\');pname.value=L.panels[pi].name;pdur.value=L.panels[pi].duration;mode.value=L.panels[pi].mode||\'contain\'}\nfunction renderPreview(){let p=L.panels[pi];preview.style.backgroundImage=p.background?`url(\'/user-images/${p.background}\')`:\'none\';preview.style.backgroundSize=p.mode==\'cover\'?\'cover\':p.mode==\'center\'?\'auto\':\'contain\';preview.innerHTML=p.elements.map((e,i)=>`<div class="el ${i==ei?\'sel\':\'\'}" style="left:${e.x}px;top:${e.y}px;font-size:${e.size}px" onmousedown="drag(event,${i})" onclick="selectEl(event,${i})"><span class="title">${e.title}</span>${V[e.label]??\'-\'} ${e.unit||\'\'}</div>`).join(\'\');propsUI()}\nfunction selectEl(ev,i){ev.stopPropagation();ei=i;renderPreview()}\nfunction propsUI(){if(ei<0){props.innerHTML=\'Element anklicken oder Sensor hinzufuegen.\';return}let e=L.panels[pi].elements[ei];props.innerHTML=`<label>Titel<input id="et" value="${e.title||\'\'}" onchange="ep()"></label><label>Sensor<input value="${e.label}" disabled></label><div class="row"><label>X<input id="ex" type="number" value="${e.x}" onchange="ep()"></label><label>Y<input id="ey" type="number" value="${e.y}" onchange="ep()"></label></div><div class="row"><label>Groesse<input id="es" type="number" value="${e.size}" onchange="ep()"></label><label>Einheit<input id="eu" value="${e.unit||\'\'}" onchange="ep()"></label></div><button class="btn" onclick="delEl()">Element loeschen</button>`}\nfunction ep(){let e=L.panels[pi].elements[ei];e.title=et.value;e.x=+ex.value;e.y=+ey.value;e.size=+es.value;e.unit=eu.value;renderPreview()}\nfunction drag(ev,i){ei=i;let e=L.panels[pi].elements[i],sx=ev.clientX,sy=ev.clientY,ox=e.x,oy=e.y;function mv(x){e.x=Math.max(0,Math.min(760,ox+x.clientX-sx));e.y=Math.max(0,Math.min(420,oy+x.clientY-sy));renderPreview()}function up(){removeEventListener(\'mousemove\',mv);removeEventListener(\'mouseup\',up)}addEventListener(\'mousemove\',mv);addEventListener(\'mouseup\',up)}\nfunction renderSensors(){let qv=(q.value||\'\').toLowerCase();sensors.innerHTML=S.filter(x=>(x.name+\' \'+x.id).toLowerCase().includes(qv)).map(x=>`<div class="sensor" onclick=\'addSensor(${JSON.stringify(x.id)},${JSON.stringify(x.name)})\'><b>${x.name}</b><br><span class="muted">${x.value}</span></div>`).join(\'\')}\nfunction addSensor(id,n){L.panels[pi].elements.push({label:id,title:n,x:60,y:60,size:24,unit:\'\'});ei=L.panels[pi].elements.length-1;renderPreview()}\nfunction delEl(){L.panels[pi].elements.splice(ei,1);ei=-1;renderPreview()}\nfunction panelProp(){let p=L.panels[pi];p.name=pname.value;p.duration=+pdur.value;p.mode=mode.value;renderPanels();renderPreview()}\nfunction addPanel(){L.panels.push({name:\'NEUES PANEL\',duration:6,background:\'\',mode:\'contain\',elements:[]});pi=L.panels.length-1;ei=-1;render()}\nasync function save(){await fetch(\'/api/layout\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify(L)});status.textContent=\'Layout gespeichert.\'}\nasync function upload(){let f=file.files[0];if(!f)return;let fd=new FormData();fd.append(\'image\',f);let j=await(await fetch(\'/api/image\',{method:\'POST\',body:fd})).json();if(j.ok){L.panels[pi].background=j.file;renderPreview();await save()}}\nasync function activate(){await save();let j=await(await fetch(\'/api/activate\',{method:\'POST\'})).json();status.textContent=j.message||j.error}\ninit();setInterval(async()=>{V=await(await fetch(\'/api/values\')).json();renderPreview()},5000)\n</script></body></html>'
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
 except:dst.unlink(missing_ok=True);return jsonify(ok=False,error="Ungueltiges Bild."),400
 return jsonify(ok=True,file=name)
@app.get("/user-images/<path:n>")
def user_image(n):return send_from_directory(IMG,n)
@app.post("/api/activate")
def activate():
 backup=""
 if MON.exists():
  b=CFG/f"monitor.backup-{int(time.time())}.json";shutil.copy2(MON,b);backup=b.name
 c=CFG/"monitor-v06-candidate.json";c.write_text(json.dumps(load_layout(),ensure_ascii=False,indent=2))
 return jsonify(ok=True,message=f"Backup: {backup or 'nicht vorhanden'}. Kandidat: {c.name}. Noch nicht automatisch auf asterctl geschaltet.")
if __name__=="__main__":app.run(host="0.0.0.0",port=8765)
