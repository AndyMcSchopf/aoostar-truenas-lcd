#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, os, shutil, time, re

CFG=Path(os.environ.get("AOOSTAR_CFG","/app/cfg"))
LAYOUT=CFG/"layout-v07.json"
VALUES=CFG/"sensors"/"values.txt"
GEN=CFG/"generated"; GEN.mkdir(parents=True,exist_ok=True)
BACK=CFG/"backups"; BACK.mkdir(parents=True,exist_ok=True)
MON=CFG/"monitor.json"
OUT=CFG/"monitor.generated.json"
W,H=960,376

THEMES={
"lcars-orange":{"bg":"#050608","panel":"#111319","orange":"#F29A49","amber":"#F6B85A","violet":"#8E7CC3","blue":"#6699CC","pink":"#C96B9A","text":"#F5EEE6"},
"lcars-classic":{"bg":"#050608","panel":"#111319","orange":"#FF9966","amber":"#FFCC99","violet":"#9999CC","blue":"#99CCFF","pink":"#CC6699","text":"#FFF4E8"}}

def vals():
 o={}
 if VALUES.exists():
  for l in VALUES.read_text(errors="replace").splitlines():
   if ":" in l:
    k,v=l.split(":",1);o[k.strip()]=v.strip()
 return o
def rgb(h):
 h=h.lstrip("#");return tuple(int(h[i:i+2],16) for i in (0,2,4))
def font(size):
 for f in ("/app/fonts/HarmonyOS_Sans_SC_Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
  if Path(f).exists():
   try:return ImageFont.truetype(f,size)
   except:pass
 return ImageFont.load_default()
def sensor(label,name,x,y,size=24,unit="",mode=1,pic=""):
 return {"decimalDigits":-1,"direction":1,"fontColor":-1,"fontFamily":"HarmonyOS_Sans_SC_Bold","fontSize":int(size),"fontWeight":"bold","height":0,"integerDigits":-1,"label":label,"maxAngle":180,"maxValue":100,"minAngle":0,"minValue":0,"mode":mode,"name":name,"pic":pic,"textAlign":"center","textDirection":0,"type":1,"unit":unit,"value":"","width":0,"x":int(x),"xz_x":0,"xz_y":0,"y":int(y)}
def render_background(panel,theme,index):
 im=Image.new("RGB",(W,H),rgb(theme["bg"]));d=ImageDraw.Draw(im)
 bg=panel.get("background")
 if bg and (CFG/"images"/bg).exists():
  src=Image.open(CFG/"images"/bg).convert("RGB"); mode=panel.get("image",{}).get("mode","cover"); zoom=float(panel.get("image",{}).get("zoom",1)); ox=int(panel.get("image",{}).get("x",0));oy=int(panel.get("image",{}).get("y",0))
  if mode=="contain":
   src.thumbnail((W,H)); px=(W-src.width)//2+ox;py=(H-src.height)//2+oy
  elif mode=="center":
   px=(W-src.width)//2+ox;py=(H-src.height)//2+oy
  else:
   sc=max(W/src.width,H/src.height)*zoom;src=src.resize((max(1,int(src.width*sc)),max(1,int(src.height*sc))))
   px=(W-src.width)//2+ox;py=(H-src.height)//2+oy
  im.paste(src,(px,py))
 for e in panel.get("elements",[]):
  typ=e.get("type"); ac=rgb(theme.get(e.get("accent","orange"),theme["orange"]));x=int(e.get("x",0));y=int(e.get("y",0));w=int(e.get("w",0));h=int(e.get("h",0))
  if typ in ("lcars_header","lcars_footer"):
   d.rounded_rectangle((x,y,x+w,y+h),radius=min(20,h//2),fill=ac);d.text((x+18,y+8),e.get("text",""),font=font(18),fill=(10,10,10))
  elif typ=="lcars_card":
   d.rounded_rectangle((x,y,x+w,y+h),radius=20,fill=rgb(theme["panel"]));d.rectangle((x,y,x+w,y+30),fill=ac);d.text((x+14,y+6),e.get("text",""),font=font(15),fill=(10,10,10))
  elif typ=="text":
   d.text((x,y),e.get("text",""),font=font(int(e.get("size",24))),fill=rgb(theme["text"]))
  elif typ=="pool":
   k=e.get("index",0);d.rounded_rectangle((x,y,x+w,y+h),radius=20,fill=rgb(theme["panel"]));d.rectangle((x,y,x+w,y+30),fill=ac);d.text((x+14,y+6),f"POOL {k+1}",font=font(15),fill=(10,10,10))
 # dynamic sensor text/bars are left to asterctl overlays
 name=f"panel_{index+1}_{re.sub('[^A-Za-z0-9]+','_',panel.get('name','panel')).strip('_').lower()}.jpg"
 im.save(GEN/name,quality=94)
 return name
def build():
 layout=json.loads(LAYOUT.read_text());theme=THEMES.get(layout.get("theme"),THEMES["lcars-orange"]);v=vals();diy=[]
 for idx,p in enumerate(layout.get("panels",[])):
  bg=render_background(p,theme,idx);ss=[]
  for e in p.get("elements",[]):
   typ=e.get("type")
   if typ=="sensor":
    ss.append(sensor(e.get("label",""),e.get("title",""),e.get("x",0),e.get("y",0),e.get("size",24),e.get("unit","")))
   elif typ=="badge":
    ss.append(sensor(e.get("label",""),"STATUS",e.get("x",0),e.get("y",0),20,""))
   elif typ=="bar":
    # asterctl native progress mode 3; generate a simple progress strip image.
    pic=f"progress_{idx}_{len(ss)}.png";strip=Image.new("RGBA",(max(10,int(e.get("w",200))),max(4,int(e.get("h",12)))),(0,0,0,0));ImageDraw.Draw(strip).rounded_rectangle((0,0,strip.width-1,strip.height-1),radius=strip.height//2,fill=rgb(theme.get(e.get("accent","orange"),theme["orange"]))+(255,));strip.save(GEN/pic)
    z=sensor(e.get("label",""),"PROGRESS",e.get("x",0),e.get("y",0),12,"",3,f"generated/{pic}");z["maxValue"]=int(e.get("max",100));ss.append(z)
   elif typ=="pool":
    n=int(e.get("index",0));ss.append(sensor(f"truenas_pool_{n}_used_percent",f"Pool {n+1}",e.get("x",0)+40,e.get("y",0)+55,28,"%"))
  diy.append({"img":f"generated/{bg}","sensor":ss,"type":5})
 out={"diy":diy,"mianban":list(range(1,len(diy)+1)),"setup":{"refresh":1,"switchTime":str(layout.get("switchTime",6))}}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2))
 return {"ok":True,"panels":len(diy),"output":str(OUT),"generated":str(GEN)}
def activate():
 if not OUT.exists():build()
 stamp=time.strftime("%Y%m%d-%H%M%S")
 if MON.exists():shutil.copy2(MON,BACK/f"monitor-before-v076-{stamp}.json")
 shutil.copy2(OUT,MON)
 return {"ok":True,"monitor":str(MON)}
if __name__=="__main__":
 import sys
 print(json.dumps(activate() if "--activate" in sys.argv else build()))
