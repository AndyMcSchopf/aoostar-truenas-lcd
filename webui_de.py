from pathlib import Path
import os,re
from flask import request,jsonify,send_from_directory
from PIL import Image
CFG=Path(os.environ.get("AOOSTAR_CFG","/app/cfg")); UPLOAD=CFG/"images"; UPLOAD.mkdir(parents=True,exist_ok=True)
ALIASES={"cpu_usage_percent":"CPU – Auslastung","temperature_cpu":"CPU – Temperatur","mem_usage_percent":"Arbeitsspeicher – Belegung","temperature_memory":"Arbeitsspeicher – Temperatur","temperature_gpu":"GPU – Temperatur","system_uptime":"System – Laufzeit","truenas_ip":"TrueNAS – IP-Adresse","truenas_iface":"LAN – Schnittstelle","truenas_net_down":"LAN – Download","truenas_net_up":"LAN – Upload","truenas_hostname":"TrueNAS – Hostname","truenas_version":"TrueNAS – Version","truenas_uptime":"TrueNAS – Laufzeit","truenas_apps_running":"Apps – aktiv","truenas_apps_stopped":"Apps – gestoppt","truenas_apps_crashed":"Apps – fehlerhaft","truenas_pool_count":"ZFS – Anzahl Pools","truenas_pools_healthy":"ZFS – gesunde Pools"}
def friendly(k):
    if k in ALIASES:return ALIASES[k]
    m=re.match(r"truenas_pool_(\d+)_(.+)",k)
    if m:
        n=int(m.group(1))+1; names={"name":"Name","status":"Status","healthy":"Gesundheit","used_percent":"Belegung","used":"Belegt","free":"Frei","size":"Größe","scan":"Scrub/Scan"}
        return f"ZFS Pool {n} – {names.get(m.group(2),m.group(2))}"
    if k.startswith("temperature_nvme_"):return "NVMe – "+k.split("_",3)[-1].replace("_"," ")+" – Temperatur"
    if k.startswith("temperature_drivetemp_"):return "HDD – "+k[len("temperature_drivetemp_"):].replace("_"," ")+" – Temperatur"
    return k
def vals():
    p=CFG/"sensors"/"values.txt"; out={}
    if p.exists():
        for line in p.read_text(errors="replace").splitlines():
            if ":" in line and "#unit" not in line:
                k,v=line.split(":",1);out[k.strip()]=v.strip()
    return out
def install_routes(app):
    @app.get("/api/de/sensors")
    def de_sensors():
        v=vals();return jsonify([{"id":k,"name":friendly(k),"value":x} for k,x in sorted(v.items(),key=lambda q:friendly(q[0]).lower())])
    @app.post("/api/de/image")
    def upload():
        f=request.files.get("image")
        if not f:return jsonify({"ok":False,"error":"Keine Bilddatei ausgewählt."}),400
        ext=Path(f.filename or "").suffix.lower()
        if ext not in (".png",".jpg",".jpeg",".webp"):return jsonify({"ok":False,"error":"Erlaubt sind PNG, JPG/JPEG und WebP."}),400
        dest=UPLOAD/("panelbild"+ext);f.save(dest)
        try:
            with Image.open(dest) as im:w,h=im.size
        except Exception:
            dest.unlink(missing_ok=True);return jsonify({"ok":False,"error":"Ungültige Bilddatei."}),400
        return jsonify({"ok":True,"path":str(dest.relative_to(CFG)),"width":w,"height":h})
    @app.get("/user-images/<path:name>")
    def user_image(name):return send_from_directory(UPLOAD,name)
    return app
