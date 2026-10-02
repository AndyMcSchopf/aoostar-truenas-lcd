#!/usr/bin/env python3
from pathlib import Path
import json,time,os
cfg=Path(os.environ.get("AOOSTAR_CFG","/app/cfg"));src=cfg/"sensors"/"values.txt";dst=cfg/"history.json"
keys=("cpu_usage_percent","temperature_cpu","mem_usage_percent","temperature_memory","truenas_net_down_bytes_sec","truenas_net_up_bytes_sec")
while True:
 try:
  vals={}
  for l in src.read_text(errors="replace").splitlines():
   if ":" in l:
    k,v=l.split(":",1);vals[k.strip()]=v.strip()
  try:h=json.loads(dst.read_text())
  except:h={}
  now=int(time.time())
  for k in keys:
   if k in vals:
    try:n=float(vals[k].replace(",","."))
    except:continue
    h.setdefault(k,[]).append({"t":now,"value":n});h[k]=h[k][-120:]
  tmp=dst.with_suffix(".tmp");tmp.write_text(json.dumps(h));tmp.replace(dst)
 except Exception as e:print("history:",e,flush=True)
 time.sleep(5)
