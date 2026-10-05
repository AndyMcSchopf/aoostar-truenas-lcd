#!/usr/bin/env python3
from flask import Flask,jsonify,request,send_from_directory,render_template
from pathlib import Path
from PIL import Image
import json,os,re,subprocess,shutil,time,hashlib,time
CFG=Path(os.environ.get("AOOSTAR_CFG","/app/cfg")); IMG=CFG/"images"; IMG.mkdir(parents=True,exist_ok=True)
PREVIEW=CFG/"lcd-preview"; PREVIEW.mkdir(parents=True,exist_ok=True)
LAYOUT=CFG/"layout-v07.json"; VALUES=CFG/"sensors"/"values.txt"; HISTORY=CFG/"history.json"
app=Flask(__name__,template_folder="/app/templates",static_folder="/app/static")
THEMES={"lcars-orange":{"name":"LCARS Orange","bg":"#050608","panel":"#111319","orange":"#F29A49","amber":"#F6B85A","violet":"#8E7CC3","blue":"#6699CC","pink":"#C96B9A","text":"#F5EEE6","muted":"#AFA7A0"},"lcars-classic":{"name":"LCARS Classic","bg":"#050608","panel":"#111319","orange":"#FF9966","amber":"#FFCC99","violet":"#9999CC","blue":"#99CCFF","pink":"#CC6699","text":"#FFF4E8","muted":"#B9AFA6"},"mono":{"name":"Monochrom","bg":"#050505","panel":"#171717","orange":"#E8E8E8","amber":"#BDBDBD","violet":"#8F8F8F","blue":"#D0D0D0","pink":"#A5A5A5","text":"#F5F5F5","muted":"#A0A0A0"}}
def vals():
 o={}
 if VALUES.exists():
  for line in VALUES.read_text(errors="replace").splitlines():
   if ":" in line:
    k,v=line.split(":",1);o[k.strip()]=v.strip()
 return o
def layout():
 if not LAYOUT.exists(): return {"schemaVersion":2,"appVersion":"0.8.1","theme":"lcars-orange","switchTime":6,"panels":[]}
 x=json.loads(LAYOUT.read_text());x["schemaVersion"]=2;x["appVersion"]="0.8.1";return x
@app.get("/")
def index(): return render_template("index.html")
@app.route("/api/layout",methods=["GET","POST"])
def api_layout():
 if request.method=="POST": LAYOUT.write_text(json.dumps(request.json,ensure_ascii=False,indent=2));return jsonify(ok=True)
 return jsonify(layout())
@app.get("/api/values")
def api_values(): return jsonify(vals())
@app.get("/api/sensors")
def sensors(): return jsonify([{"id":k,"name":k.replace("_"," ").title(),"value":v} for k,v in sorted(vals().items()) if "#unit" not in k])
@app.get("/api/themes")
def themes(): return jsonify(THEMES)
@app.get("/api/history")
def history():
 try:return jsonify(json.loads(HISTORY.read_text()))
 except:return jsonify({})
@app.route("/api/images",methods=["GET","POST"])
def images():
 if request.method=="GET":
  out=[]
  for f in sorted(IMG.iterdir()):
   if f.suffix.lower() in (".png",".jpg",".jpeg",".webp"):
    try:
     with Image.open(f) as im:w,h=im.size
     out.append({"name":f.name,"width":w,"height":h})
    except:pass
  return jsonify(out)
 f=request.files.get("image")
 if not f:return jsonify(error="Keine Datei"),400
 name=re.sub(r"[^A-Za-z0-9._-]+","_",Path(f.filename).name);dst=IMG/name;f.save(dst)
 try:
  with Image.open(dst) as im:im.verify()
 except:dst.unlink(missing_ok=True);return jsonify(error="Ungueltiges Bild"),400
 return jsonify(ok=True,file=name)
@app.delete("/api/images/<path:name>")
def delete_image(name):(IMG/Path(name).name).unlink(missing_ok=True);return jsonify(ok=True)
@app.get("/user-images/<path:name>")
def user_image(name):return send_from_directory(IMG,name)
def preview_images():
 return [{"name":f.name,"url":"/lcd-preview/"+f.name+"?v="+str(f.stat().st_mtime_ns)} for f in sorted(PREVIEW.glob("*.png"))]

@app.get("/lcd-preview/<path:name>")
def lcd_preview_file(name): return send_from_directory(PREVIEW,Path(name).name)

@app.get("/api/lcd/preview")
def lcd_preview_list(): return jsonify(images=preview_images())

def _png_hash(p):
 try:return hashlib.sha256(p.read_bytes()).hexdigest()
 except:return ""

def _snapshot_pngs(seen,captures,events):
 # Capture every new/changed PNG immediately, before asterctl can overwrite it.
 now=time.monotonic()
 candidates=[p for p in PREVIEW.rglob("*.png") if "capture-" not in p.name]
 for p in candidates:
  try:
   st=p.stat();sig=(st.st_size,st.st_mtime_ns,_png_hash(p))
  except FileNotFoundError:continue
  key=str(p)
  if seen.get(key)==sig:continue
  seen[key]=sig
  dst=PREVIEW/f"capture-{len(captures)+1:02d}.png"
  shutil.copy2(p,dst)
  captures.append(dst)
  events.append({"t":round(now,3),"source":str(p.relative_to(PREVIEW)),"capture":dst.name,
                 "bytes":st.st_size,"mtime_ns":st.st_mtime_ns,"sha256":sig[2]})
 return captures

def _asterctl_preview(expected_panels):
 cmd=["asterctl","--simulate","--save","--config",str(CFG/"monitor.generated.json"),
      "--config-dir",str(CFG),"--font-dir","/app/fonts","--sensor-path",str(CFG/"sensors"),
      "--sensor-mapping",str(CFG/"sensor-mapping.cfg")]
 p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=str(PREVIEW))
 deadline=time.monotonic()+max(16.0,expected_panels*5.0)
 seen={};captures=[];events=[]
 try:
  while time.monotonic()<deadline:
   time.sleep(.15)
   _snapshot_pngs(seen,captures,events)
   # We may capture intermediate frames, so stop only after at least expected distinct hashes.
   distinct=[]
   hashes=set()
   for c in captures:
    h=_png_hash(c)
    if h and h not in hashes:hashes.add(h);distinct.append(c)
   if len(distinct)>=expected_panels:break
   if p.poll() is not None:break
 finally:
  if p.poll() is None:
   p.terminate()
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:
    p.kill();p.wait(timeout=2)
 stdout,stderr=p.communicate()
 _snapshot_pngs(seen,captures,events)
 # Deduplicate exact frames while preserving first-seen order.
 unique=[];hashes=set()
 for c in captures:
  h=_png_hash(c)
  if h and h not in hashes:
   hashes.add(h);unique.append(c)
 # Normalize names used by the web overlay.
 for old in list(PREVIEW.glob("preview-*.png")):old.unlink(missing_ok=True)
 images=[]
 for i,c in enumerate(unique,1):
  dst=PREVIEW/f"preview-{i:02d}.png";shutil.copy2(c,dst)
  images.append({"name":dst.name,"url":"/lcd-preview/"+dst.name+"?v="+str(dst.stat().st_mtime_ns)})
 return p.returncode,images,(stdout or "")[-8000:],(stderr or "")[-8000:],events

@app.post("/api/lcd/generate")
def generate():
 try:
  r=subprocess.run(["python3","/app/lcd_generator.py"],capture_output=True,text=True,timeout=30)
  if r.returncode!=0:return jsonify(ok=False,error="lcd_generator.py fehlgeschlagen",detail=r.stderr[-4000:]),500
  base=json.loads(r.stdout.strip().splitlines()[-1])
  for f in PREVIEW.rglob("*"):
   if f.is_file():f.unlink(missing_ok=True)
  try:
   cfg=json.loads((CFG/"monitor.generated.json").read_text())
   expected=len(cfg.get("diy",[]))
  except Exception:
   expected=int(base.get("panels",1) or 1)
  rc,images,out,err,events=_asterctl_preview(max(1,expected))
  base["asterctlPreviewLog"]=(out+"\n"+err)[-4000:]
  base["expectedPanels"]=expected
  base["previewCaptureEvents"]=events
  if images:
   base["previewMode"]="asterctl-simulate"
   base["previewImages"]=images
   base["previewComplete"]=len(images)>=expected
   base["capturedFrames"]=len(images)
   if len(images)<expected:base["previewWarning"]=f"asterctl erzeugte nur {len(images)} von {expected} erwarteten Preview-Panels."
   return jsonify(base)
  # Explicit fallback, never pretend it is the real LCD render.
  for f in sorted((CFG/"generated").glob("panel_*.png")):shutil.copy2(f,PREVIEW/f.name)
  base["previewMode"]="generated-background-fallback"
  base["previewImages"]=preview_images()
  base["previewComplete"]=False
  base["previewWarning"]="asterctl --simulate --save erzeugte innerhalb von 12 Sekunden kein auffindbares PNG."
  return jsonify(base)
 except subprocess.TimeoutExpired as e:
  return jsonify(ok=False,error="LCD Preview Backend Timeout",detail=str(e)),504
 except Exception as e:
  app.logger.exception("LCD preview failed")
  return jsonify(ok=False,error="LCD Preview Backend Fehler",detail=str(e)),500

@app.post("/api/lcd/activate")
def activate():
 r=subprocess.run(["python3","/app/lcd_generator.py","--activate"],capture_output=True,text=True,timeout=30)
 if r.returncode!=0:return jsonify(ok=False,error=r.stderr),500
 result=json.loads(r.stdout.strip().splitlines()[-1])
 try:
  reload_flag=Path("/run/aoostar/reload-lcd")
  reload_flag.parent.mkdir(parents=True,exist_ok=True)
  reload_flag.write_text(str(time.time()))
  result["reloadRequested"]=True
 except Exception as e:
  result["reloadRequested"]=False;result["reloadError"]=str(e)
 return jsonify(result)
if __name__=="__main__":app.run(host="0.0.0.0",port=8765)
