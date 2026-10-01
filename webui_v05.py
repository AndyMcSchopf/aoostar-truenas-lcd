#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory, Response
from pathlib import Path
from PIL import Image
import json, os, re

app=Flask(__name__)
CFG=Path(os.environ.get("AOOSTAR_CFG","/app/cfg"))
SENS=CFG/"sensors"/"values.txt"
IMG=CFG/"images"; IMG.mkdir(parents=True,exist_ok=True)
PRESET=Path("/app/presets/truenas-de-v0.5.json")

ALIASES={
"cpu_usage_percent":"CPU – Auslastung","temperature_cpu":"CPU – Temperatur",
"mem_usage_percent":"RAM – Belegung","temperature_memory":"RAM – Temperatur",
"temperature_gpu":"GPU – Temperatur","system_uptime":"System – Laufzeit",
"truenas_ip":"TrueNAS – IP-Adresse","truenas_iface":"LAN – Schnittstelle",
"truenas_net_down":"LAN – Download","truenas_net_up":"LAN – Upload",
"truenas_hostname":"TrueNAS – Hostname","truenas_version":"TrueNAS – Version",
"truenas_uptime":"TrueNAS – Laufzeit","truenas_system_status":"TrueNAS – Systemstatus",
"truenas_apps_running":"Apps – aktiv","truenas_apps_stopped":"Apps – gestoppt",
"truenas_apps_crashed":"Apps – fehlerhaft","truenas_apps_updates":"Apps – Updates verfügbar",
"truenas_pool_count":"ZFS – Anzahl Pools","truenas_pools_healthy":"ZFS – gesunde Pools",
"truenas_scrub_de":"ZFS – Scrub-Status"}

def values():
    out={}
    if SENS.exists():
        for ln in SENS.read_text(errors="replace").splitlines():
            if ":" in ln:
                k,v=ln.split(":",1); out[k.strip()]=v.strip()
    return out

def friendly(k):
    if k in ALIASES:return ALIASES[k]
    m=re.match(r"truenas_pool_(\d+)_(.+)",k)
    if m:
        n=int(m.group(1))+1
        names={"name":"Name","status":"Status","healthy":"Gesund","used_percent":"Belegung",
               "used":"Belegt","free":"Frei","size":"Größe","scan":"Scrub"}
        return f"ZFS Pool {n} – {names.get(m.group(2),m.group(2))}"
    if k.startswith("temperature_nvme_"):
        return "NVMe – "+k.split("_",3)[-1].replace("_"," ")+" – Temperatur"
    if k.startswith("temperature_drivetemp_"):
        return "HDD – "+k[len("temperature_drivetemp_"):].replace("_"," ")+" – Temperatur"
    return k

HTML=r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AOOSTAR TrueNAS LCD</title>
<style>
body{font-family:Arial,sans-serif;background:#111827;color:#e5e7eb;margin:0}
header{padding:18px 24px;background:#0b1220;border-bottom:1px solid #374151}
main{padding:22px;max-width:1400px;margin:auto}
.tabs button,.btn{background:#1f2937;color:#fff;border:1px solid #4b5563;border-radius:7px;padding:9px 13px;margin:3px;cursor:pointer}
.tabs button.active,.btn.primary{background:#374151}
.card{background:#182131;border:1px solid #374151;border-radius:10px;padding:16px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}
.sensor{padding:9px;border-bottom:1px solid #303a49}.sensor b{display:block}.muted{color:#9ca3af}
.preview{background:#05080d;border:1px solid #4b5563;aspect-ratio:16/9;max-width:800px;padding:22px;box-sizing:border-box}
.pool{margin:10px 0}.bar{height:14px;background:#374151;border-radius:8px;overflow:hidden}.fill{height:100%;background:#9ca3af}
input,select{background:#111827;color:#fff;border:1px solid #4b5563;border-radius:6px;padding:8px}
.ok{color:#86efac}.warn{color:#fde68a}.bad{color:#fca5a5}
</style></head><body><header><h2>AOOSTAR TrueNAS LCD – Editor</h2>
<div class="muted">TrueNAS SCALE · deutsches Dashboard · Webeditor v0.5</div></header><main>
<div class="tabs"><button class="active" onclick="show('dash',this)">Dashboard</button>
<button onclick="show('panels',this)">Panels</button><button onclick="show('sensors',this)">Sensoren</button>
<button onclick="show('image',this)">Bild-Panel</button><button onclick="show('io',this)">Import / Export</button></div>
<section id="dash" class="page"><div class="grid">
<div class="card"><h3>System</h3><div id="system"></div></div>
<div class="card"><h3>TrueNAS</h3><div id="tn"></div></div></div>
<div class="card"><h3>ZFS Pools</h3><div id="pools"></div></div></section>
<section id="panels" class="page" style="display:none"><div class="card"><h3>Vier-Panel-Preset</h3>
<p>SYSTEM · SPEICHER / ZFS · TRUENAS · BILD</p>
<p>Das Preset überschreibt deine aktuelle Konfiguration nicht automatisch.</p>
<button class="btn primary" onclick="downloadPreset()">Preset herunterladen</button></div></section>
<section id="sensors" class="page" style="display:none"><div class="card"><h3>Verfügbare Sensoren</h3><input id="q" placeholder="Sensor suchen…" oninput="renderSensors()"><div id="sensorlist"></div></div></section>
<section id="image" class="page" style="display:none"><div class="card"><h3>Bild-Panel</h3>
<p>PNG, JPG/JPEG oder WebP. Die Datei bleibt im persistenten Config-Volume erhalten.</p>
<input type="file" id="file" accept=".png,.jpg,.jpeg,.webp,image/*">
<select id="mode"><option value="contain">Einpassen</option><option value="cover">Ausfüllen / zuschneiden</option><option value="center">Originalgröße / zentriert</option></select>
<button class="btn primary" onclick="upload()">Bild hochladen</button><div id="uploadResult" class="muted"></div>
<p>Live-Sensoren können im nächsten Editor-Schritt über das Bild gelegt werden.</p></div></section>
<section id="io" class="page" style="display:none"><div class="card"><h3>Import / Export</h3>
<button class="btn" onclick="location='/api/preset'">Deutsches Preset exportieren</button>
<p class="muted">Die bestehende Legacy-Konfiguration wird in v0.5 absichtlich nicht automatisch verändert.</p></div></section>
</main><script>
let vals={}, sensors=[];
function show(id,b){document.querySelectorAll('.page').forEach(x=>x.style.display='none');document.getElementById(id).style.display='block';document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
async function refresh(){vals=await (await fetch('/api/values')).json();sensors=await (await fetch('/api/sensors')).json();render();renderSensors()}
function row(n,k,u=''){let v=vals[k]??'–';return `<div class="sensor"><b>${n}</b>${v}${u}</div>`}
function render(){document.getElementById('system').innerHTML=row('CPU','cpu_usage_percent',' %')+row('CPU-Temperatur','temperature_cpu',' °C')+row('RAM','mem_usage_percent',' %')+row('GPU','temperature_gpu',' °C')+row('Download','truenas_net_down')+row('Upload','truenas_net_up');
document.getElementById('tn').innerHTML=row('Hostname','truenas_hostname')+row('Version','truenas_version')+row('Systemstatus','truenas_system_status')+row('Apps aktiv','truenas_apps_running')+row('App-Updates','truenas_apps_updates');
let h='';for(let i=0;i<8;i++){let n=vals[`truenas_pool_${i}_name`];if(!n)continue;let p=parseFloat(vals[`truenas_pool_${i}_used_percent`]||0);h+=`<div class="pool"><b>${n}</b> · ${vals[`truenas_pool_${i}_status`]||''} · ${p}%<div class="bar"><div class="fill" style="width:${Math.min(100,p)}%"></div></div><span class="muted">${vals[`truenas_pool_${i}_used`]||''} belegt · ${vals[`truenas_pool_${i}_free`]||''} frei · ${vals[`truenas_pool_${i}_scan`]||''}</span></div>`}document.getElementById('pools').innerHTML=h}
function renderSensors(){let q=(document.getElementById('q')?.value||'').toLowerCase();document.getElementById('sensorlist').innerHTML=sensors.filter(s=>(s.name+' '+s.id).toLowerCase().includes(q)).map(s=>`<div class="sensor"><b>${s.name}</b><span class="muted">${s.id}</span><br>${s.value}</div>`).join('')}
async function upload(){let f=document.getElementById('file').files[0];if(!f)return;let fd=new FormData();fd.append('image',f);fd.append('mode',document.getElementById('mode').value);let r=await fetch('/api/image',{method:'POST',body:fd});let j=await r.json();document.getElementById('uploadResult').textContent=j.ok?'Gespeichert: '+j.path:j.error}
function downloadPreset(){location='/api/preset'}
refresh();setInterval(refresh,5000);
</script></body></html>"""

@app.get("/")
def index(): return Response(HTML,mimetype="text/html")
@app.get("/api/values")
def api_values(): return jsonify(values())
@app.get("/api/sensors")
def api_sensors():
    v=values(); return jsonify([{"id":k,"name":friendly(k),"value":x} for k,x in sorted(v.items(),key=lambda z:friendly(z[0]).lower()) if "#unit" not in k])
@app.get("/api/preset")
def preset(): return send_from_directory(PRESET.parent,PRESET.name,as_attachment=True)
@app.post("/api/image")
def image():
    f=request.files.get("image"); mode=request.form.get("mode","contain")
    if not f:return jsonify(ok=False,error="Keine Bilddatei ausgewählt."),400
    ext=Path(f.filename or "").suffix.lower()
    if ext not in (".png",".jpg",".jpeg",".webp"):return jsonify(ok=False,error="Erlaubt sind PNG, JPG/JPEG und WebP."),400
    dst=IMG/("panelbild"+ext); f.save(dst)
    try:
        with Image.open(dst) as im:w,h=im.size
    except Exception:
        dst.unlink(missing_ok=True);return jsonify(ok=False,error="Ungültige Bilddatei."),400
    meta={"file":dst.name,"mode":mode,"width":w,"height":h}
    (IMG/"panelbild.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    return jsonify(ok=True,path=f"images/{dst.name}",**meta)
if __name__=="__main__": app.run(host="0.0.0.0",port=8765)
