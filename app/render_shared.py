from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
W,H=960,376
def image_rect(iw,ih,mode,zoom,x,y):
 b=max(W/iw,H/ih) if mode=="cover" else min(W/iw,H/ih) if mode=="contain" else 1.;s=b*float(zoom or 1);w=iw*s;h=ih*s;return w,h,(W-w)/2+float(x or 0),(H-h)/2+float(y or 0)
def font(n):
 p="/app/fonts/HarmonyOS_Sans_SC_Bold.ttf"
 return ImageFont.truetype(p,int(n)) if Path(p).exists() else ImageFont.load_default()
def rgb(h):h=h.lstrip("#");return tuple(int(h[i:i+2],16) for i in (0,2,4))
def spark(im,box,vals,color,maxv=None,minv=0):
 nums=[]
 for item in vals[-60:]:
  raw=item.get("value",item) if isinstance(item,dict) else item
  try: nums.append(float(str(raw).replace(",",".")))
  except Exception: continue
 if len(nums)<2:return
 x,y,w,h=box;lo=float(minv or 0);hi=float(maxv) if maxv not in (None,"") else max(max(nums),1);span=max(0.000001,hi-lo)
 pts=[(x+i/(len(nums)-1)*w,y+h-min(1,max(0,(v-lo)/span))*h) for i,v in enumerate(nums)]
 o=Image.new("RGBA",(W,H));d=ImageDraw.Draw(o);c=rgb(color);d.polygon([(x,y+h)]+pts+[(x+w,y+h)],fill=c+(42,));d.line(pts,fill=c+(255,),width=3);im.alpha_composite(o)
