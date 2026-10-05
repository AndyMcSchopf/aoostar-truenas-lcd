from app.lcd_compile_v12 import compact_uptime, lcd_sensor, clean_generated, write_report
#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json,os,shutil,time
from render_shared import W,H,image_rect,font,rgb,spark
C=Path(os.environ.get("AOOSTAR_CFG","/app/cfg"));G=C/"generated";G.mkdir(parents=True,exist_ok=True);O=C/"monitor.generated.json";M=C/"monitor.json";B=C/"backups";B.mkdir(exist_ok=True)
T={"bg":"#050608","panel":"#111319","orange":"#F29A49","amber":"#F6B85A","violet":"#8E7CC3","blue":"#6699CC","pink":"#C96B9A","text":"#F5EEE6","muted":"#AFA7A0"}
def readvals():
 o={}
 p=C/"sensors/values.txt"
 if p.exists():
  for l in p.read_text(errors="replace").splitlines():
   if ":" in l:k,v=l.split(":",1);o[k.strip()]=v.strip()
 return o
def hist():
 try:return json.loads((C/"history.json").read_text())
 except:return {}
def sen(e):return{"decimalDigits":-1,"direction":1,"fontColor":-1,"fontFamily":"HarmonyOS_Sans_SC_Bold","fontSize":int(e.get("size",24)),"fontWeight":"bold","height":0,"integerDigits":-1,"label":e.get("label",""),"maxAngle":180,"maxValue":100,"minAngle":0,"minValue":0,"mode":1,"name":e.get("title",""),"pic":"","textAlign":"center","textDirection":0,"type":1,"unit":e.get("unit",""),"value":"","width":0,"x":int(e.get("x",0)),"xz_x":0,"xz_y":0,"y":int(e.get("y",0))}
def panel(p,i,v,h):
 im=Image.new("RGBA",(W,H),rgb(T["bg"])+(255,))
 bg=p.get("background");m=p.get("image",{})
 if bg and (C/"images"/bg).exists():
  s=Image.open(C/"images"/bg).convert("RGBA");rw,rh,x,y=image_rect(s.width,s.height,m.get("mode","cover"),m.get("zoom",1),m.get("x",0),m.get("y",0));s=s.resize((round(rw),round(rh)));im.alpha_composite(s,(round(x),round(y)))
 d=ImageDraw.Draw(im)
 for e in p.get("elements",[]):
  q=e.get("type");a=T.get(e.get("accent","orange"),T["orange"]);x=int(e.get("x",0));y=int(e.get("y",0));w=int(e.get("w",0));hh=int(e.get("h",0))
  if q=="header":d.rounded_rectangle((x,y,x+w,y+hh),radius=min(20,hh//2),fill=rgb(a));d.text((x+16,y+8),e.get("text",""),font=font(17),fill=(10,10,10))
  elif q=="card":d.rounded_rectangle((x,y,x+w,y+hh),radius=20,fill=rgb(T["panel"]));d.rectangle((x,y,x+w,y+30),fill=rgb(a));d.text((x+14,y+5),e.get("text",""),font=font(15),fill=(10,10,10))
  elif q=="pool":
   n=int(e.get("index",0));k=f"truenas_pool_{n}_";pct=float(v.get(k+"used_percent",0) or 0);col="#CC6666" if pct>=90 else "#FFCC66" if pct>=75 else a
   d.rounded_rectangle((x,y,x+w,y+hh),radius=20,fill=rgb(T["panel"]));d.rectangle((x,y,x+w,y+30),fill=rgb(col));d.text((x+14,y+5),f'{v.get(k+"name","POOL")} · {v.get(k+"status","")}',font=font(13),fill=(10,10,10));d.text((x+18,y+42),f"{pct:.0f}%",font=font(25),fill=rgb(T["text"]));d.text((x+100,y+49),f'{v.get(k+"used","")} / {v.get(k+"size","")}',font=font(12),fill=rgb(T["muted"]));d.rounded_rectangle((x+18,y+88,x+w-18,y+99),5,fill=(45,49,57));d.rounded_rectangle((x+18,y+88,x+18+(w-36)*pct/100,y+99),5,fill=rgb(col))
  elif q=="sparkline":spark(im,(x,y,w,hh),h.get(e.get("label"),[]),a,e.get("max"))
  elif q=="text":d.text((x,y),e.get("text",""),font=font(e.get("size",24)),fill=rgb(T["text"]))
 fn=f"panel_{i+1}.png";im.convert("RGB").save(G/fn);return fn
def build():`n clean_generated(CFG)
 L=json.loads((C/"layout-v07.json").read_text());v=readvals();h=hist();d=[]
 for i,p in enumerate(L.get("panels",[])):
  fn=panel(p,i,v,h);ss=[sen(e) for e in p.get("elements",[]) if e.get("type")=="sensor"]
  d.append({"img":f"generated/{fn}","sensor":ss,"type":5})
 O.write_text(json.dumps({"diy":d,"mianban":list(range(1,len(d)+1)),"setup":{"refresh":1,"switchTime":str(L.get("switchTime",6))}},ensure_ascii=False,indent=2));return{"ok":True,"panels":len(d)}
def activate():
 r=build();stamp=time.strftime("%Y%m%d-%H%M%S")
 if M.exists():shutil.copy2(M,B/f"monitor-before-activate-{stamp}.json")
 shutil.copy2(O,M);return r
if __name__=="__main__":
 import sys;print(json.dumps(activate() if "--activate" in sys.argv else build()))
