#!/usr/bin/env python3
from pathlib import Path
import json,time,os
cfg=Path(os.environ.get("AOOSTAR_CFG","/app/cfg"));src=cfg/"sensors"/"values.txt";dst=cfg/"history.json";layout=cfg/"layout-v07.json"
BASE={"cpu_usage_percent","temperature_cpu","mem_usage_percent","temperature_memory","truenas_net_down_bytes_sec","truenas_net_up_bytes_sec"}
def keys():
 k=set(BASE)
 try:
  L=json.loads(layout.read_text())
  for p in L.get("panels",[]):
   for e in p.get("elements",[]):
    if e.get("type")=="sparkline" and e.get("label"): k.add(e["label"])
 except Exception: pass
 return k
while True:
 try:
  vals={}
  for line in src.read_text(errors="replace").splitlines():
   if ":" in line:
    k,v=line.split(":",1);vals[k.strip()]=v.strip()
  try: hist=json.loads(dst.read_text())
  except: hist={}
  now=int(time.time())
  for k in keys():
   if k in vals:
    try:n=float(vals[k].replace(",","."))
    except:continue
    hist.setdefault(k,[]).append({"t":now,"value":n});hist[k]=hist[k][-120:]
  tmp=dst.with_suffix(".tmp");tmp.write_text(json.dumps(hist));tmp.replace(dst)
 except Exception as ex:print("history:",ex,flush=True)
 time.sleep(5)
