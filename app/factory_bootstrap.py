#!/usr/bin/env python3
from pathlib import Path
import json, os, shutil, subprocess
CFG=Path(os.environ.get("AOOSTAR_CFG","/app/cfg"))
DEFAULT=Path("/defaults/factory/layout-v07.json")
LAYOUT=CFG/"layout-v07.json"
MONITOR=CFG/"monitor.json"
def valid_layout(p):
 try:
  j=json.loads(p.read_text()); return isinstance(j.get("panels"),list) and len(j["panels"])>0
 except:return False
def main():
 CFG.mkdir(parents=True,exist_ok=True)
 for d in ("sensors","images","backups"): (CFG/d).mkdir(exist_ok=True)
 created=False
 if not valid_layout(LAYOUT):
  shutil.copy2(DEFAULT,LAYOUT);created=True
  print("[bootstrap] installed factory layout: 4 panels")
 if not MONITOR.exists() or MONITOR.stat().st_size==0:
  r=subprocess.run(["python3","/app/lcd_generator.py","--activate"],capture_output=True,text=True)
  if r.returncode!=0:
   print("[bootstrap] initial monitor generation failed:",r.stderr.strip(),flush=True)
   return 1
  print("[bootstrap] generated initial monitor.json")
 return 0
if __name__=="__main__":raise SystemExit(main())
