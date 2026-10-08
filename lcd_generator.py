import re
#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw
import json, os, shutil, time
from render_shared import W, H, image_rect, font, rgb, spark

C = Path(os.environ.get("AOOSTAR_CFG", "/app/cfg"))
G = C / "generated"
O = C / "monitor.generated.json"
M = C / "monitor.json"
B = C / "backups"
T = {"bg":"#050608","panel":"#111319","orange":"#F29A49","amber":"#F6B85A",
     "violet":"#8E7CC3","blue":"#6699CC","pink":"#C96B9A","text":"#F5EEE6","muted":"#AFA7A0"}

def text_rgb(name, default="white"):
    if not name or name in ("auto","white"): return rgb(T["text"])
    if name=="muted": return rgb(T["muted"])
    if name=="green": return (102,204,153)
    return rgb(T.get(name, T["text"]))

def clean_generated():
    if G.exists(): shutil.rmtree(G)
    G.mkdir(parents=True, exist_ok=True)
    B.mkdir(parents=True, exist_ok=True)

def readvals():
    out = {}
    p = C / "sensors" / "values.txt"
    if p.exists():
        for line in p.read_text(errors="replace").splitlines():
            if ":" in line:
                k, v = line.split(":", 1); out[k.strip()] = v.strip()
    return out

def numeric(value, default=0.0):
    """Match browser parseFloat semantics for sensor strings with units/commas."""
    if isinstance(value, (int, float)): return float(value)
    s=str(value or "").strip().replace(",", ".")
    m=re.match(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)", s)
    try: return float(m.group(0)) if m else float(default)
    except Exception: return float(default)

def hist():
    try: return json.loads((C / "history.json").read_text())
    except Exception: return {}

def textbox(e, native=False):
    size = int(e.get("size", 24))
    x, y = int(e.get("x", 0)), int(e.get("y", 0))
    if native:
        # v0.8 contract: editor x/y describe the upper-left corner of a real text box.
        # Prefer explicit w/h. If absent, use a conservative LCD-first box.
        w = int(e.get("w") or max(72, round(size * 3.4)))
        h = int(e.get("h") or max(34, round(size * 1.45)))
        align = e.get("align", "center")
    else:
        # Compatibility path for panels 2-4: preserve v0.7.x behavior exactly.
        w = int(e.get("w", 0) or 0); h = int(e.get("h", 0) or 0); align = "center"
    return x, y, w, h, align

def label_metrics(e):
    title = str(e.get("title", "")).strip()
    size = int(e.get("size", 24))
    label_size = int(e.get("titleSize", max(15, min(18, int(size * 0.48)))))
    gap = 4
    return title, label_size, gap

def sensor_json(e, native=False):
    x, y, w, h, align = textbox(e, native)
    label = e.get("label", "")
    title, label_size, gap = label_metrics(e)
    if native and title:
        # Universal contract: editor x/y is the top of label+value block.
        # asterctl renders only the live value, so move it below the static label.
        y += label_size + gap
        h = max(24, h - label_size - gap)
    if native and label == "truenas_uptime": label = "truenas_uptime_short"
    return {
        "decimalDigits": int(e.get("decimalDigits", -1)), "direction": 1, "fontColor": e.get("fontColor", -1),
        "fontFamily": "HarmonyOS_Sans_SC_Bold", "fontSize": int(e.get("size", 24)),
        "fontWeight": "bold", "height": h, "integerDigits": int(e.get("integerDigits", -1)),
        "label": label, "maxAngle": 180, "maxValue": 100, "minAngle": 0, "minValue": 0,
        "mode": 1, "name": "", "pic": "", "textAlign": align,
        "textDirection": 0, "type": 1, "unit": e.get("unit", ""), "value": "",
        "width": w, "x": x, "xz_x": 0, "xz_y": 0, "y": y
    }

def draw_static_label(d, e):
    title, label_size, gap = label_metrics(e)
    if not title: return
    x, y = int(e.get("x", 0)), int(e.get("y", 0))
    size = int(e.get("size", 24))
    w = int(e.get("w") or max(72, round(size * 3.4)))
    align = str(e.get("titleAlign", "left")).lower()
    f = font(label_size)
    bb = d.textbbox((0, 0), title, font=f)
    tw = max(0, bb[2] - bb[0])
    if align == "center":
        tx = x + max(0, (w - tw) // 2)
    elif align == "right":
        tx = x + max(0, w - tw)
    else:
        tx = x
    d.text((tx, y), title, font=f, fill=text_rgb(e.get("titleColor","muted"),"muted"))

def panel(p, i, values, history):
    im = Image.new("RGBA", (W, H), rgb(T["bg"]) + (255,))
    bg = p.get("background"); m = p.get("image", {})
    if bg and (C / "images" / bg).exists():
        src = Image.open(C / "images" / bg).convert("RGBA")
        rw, rh, ox, oy = image_rect(src.width, src.height, m.get("mode", "cover"), m.get("zoom", 1), m.get("x", 0), m.get("y", 0))
        src = src.resize((round(rw), round(rh))); im.alpha_composite(src, (round(ox), round(oy)))
    d = ImageDraw.Draw(im)
    native = any(e.get("type") in ("sensor", "badge") for e in p.get("elements", []))
    for e in p.get("elements", []):
        q = e.get("type"); a = T.get(e.get("accent", "orange"), T["orange"])
        x, y, w, hh = int(e.get("x",0)), int(e.get("y",0)), int(e.get("w",0)), int(e.get("h",0))
        if q in ("header", "lcars_header"):
            d.rounded_rectangle((x,y,x+w,y+hh), radius=min(20,max(1,hh//2)), fill=rgb(a))
            d.text((x+16,y+8), e.get("text",""), font=font(int(e.get("size",18))), fill=text_rgb(e.get("textColor","auto")))
        elif q == "card":
            radius = min(20, max(1, hh // 2))
            d.rounded_rectangle((x,y,x+w,y+hh),radius=radius,fill=rgb(T["panel"]))
            # Rounded top corners, square lower edge: same visual contract as editor cardhead.
            d.rounded_rectangle((x,y,x+w,y+30),radius=min(radius,15),fill=rgb(a))
            d.rectangle((x,y+15,x+w,y+30),fill=rgb(a))
            d.text((x+14,y+5),e.get("text",""),font=font(int(e.get("size",15))),fill=text_rgb(e.get("textColor","auto")))
        elif q == "pool":
            n=int(e.get("index",0)); k=f"truenas_pool_{n}_"; pct=float(values.get(k+"used_percent",0) or 0); col="#CC6666" if pct>=90 else "#FFCC66" if pct>=75 else a
            name_size=int(e.get("nameSize",15)); pct_size=int(e.get("percentSize",25)); cap_size=int(e.get("capacitySize",18)); fmt=e.get("capacityFormat","compact")
            used=str(values.get(k+"used","")); total=str(values.get(k+"size","")); free=str(values.get(k+"free",""))
            if fmt=="full": cap=f"{used} / {total}"
            elif fmt=="usedfree": cap=f"BELEGT {used}  FREI {free}"
            else:
                short_used=re.sub(r"\s+(TiB|GiB|MiB)$","",used)
                cap=f"{short_used} / {total}"
            d.rounded_rectangle((x,y,x+w,y+hh),radius=20,fill=rgb(T["panel"]))
            d.rounded_rectangle((x,y,x+w,y+30),radius=15,fill=rgb(col))
            d.rectangle((x,y+15,x+w,y+30),fill=rgb(col))
            d.text((x+14,y+5),f'{values.get(k+"name","POOL")} · {values.get(k+"status","")}',font=font(name_size),fill=(10,10,10))
            pct_text=f"{pct:.0f}%"
            pct_bbox=d.textbbox((0,0),pct_text,font=font(pct_size))
            cap_x=max(x+100,x+18+(pct_bbox[2]-pct_bbox[0])+16)
            d.text((x+18,y+42),pct_text,font=font(pct_size),fill=rgb(T["text"]))
            d.text((cap_x,y+49),cap,font=font(cap_size),fill=text_rgb(e.get("titleColor","muted"),"muted"))
            d.rounded_rectangle((x+18,y+88,x+w-18,y+99),5,fill=(45,49,57))
            d.rounded_rectangle((x+18,y+88,x+18+(w-36)*pct/100,y+99),5,fill=rgb(col))
        elif q == "bar":
            value=numeric(values.get(e.get("label"),0),0)
            minimum=numeric(e.get("min",0),0); maximum=numeric(e.get("max",100),100); pct=max(0.0,min(1.0,(value-minimum)/max(0.000001,maximum-minimum)))
            d.rounded_rectangle((x,y,x+w,y+hh),radius=max(1,min(hh//2,6)),fill=(45,49,57))
            if pct>0: d.rounded_rectangle((x,y,x+round(w*pct),y+hh),radius=max(1,min(hh//2,6)),fill=rgb(a))
        elif q == "sparkline": spark(im,(x,y,w,hh),history.get(e.get("label"),[]),a,e.get("max"),e.get("min",0))
        elif q == "text": d.text((x,y),e.get("text",""),font=font(int(e.get("size",24))),fill=text_rgb(e.get("textColor","auto")))
        elif q in ("sensor", "badge"):
            draw_static_label(d, e)
    fn = f"panel_{i+1}.png"; im.convert("RGB").save(G / fn); return fn

def status_sensors(e):
    y=int(e.get("y",0)); total_h=int(e.get("h",62)); status_size=int(e.get("size",22)); detail_size=int(e.get("detailSize",12)); gap=int(e.get("detailGap",6))
    main_h=max(18, round(status_size*1.35)); detail_h=max(18, round(detail_size*1.35))
    main=dict(e); main["title"]=""; main["unit"]=""; main["size"]=status_size; main["align"]=e.get("align","center"); main["y"]=y; main["h"]=min(total_h,main_h)
    out=[sensor_json(main, True)]
    detail=e.get("detailLabel","")
    if detail:
        detail_y=y+main_h+gap; remaining=max(18,total_h-main_h-gap)
        d=dict(e); d["label"]=detail; d["title"]=""; d["unit"]=""; d["size"]=detail_size; d["align"]=e.get("align","center"); d["y"]=detail_y; d["h"]=min(remaining,detail_h)
        out.append(sensor_json(d, True))
    return out

def build():
    clean_generated()
    layout = json.loads((C / "layout-v07.json").read_text()); values = readvals(); history = hist(); diy = []
    for i, p in enumerate(layout.get("panels", [])):
        fn = panel(p, i, values, history)
        elements = p.get("elements", [])
        native = any(e.get("type") in ("sensor", "badge") for e in elements)
        sensors = []
        for e in elements:
            if e.get("type")=="sensor": sensors.append(sensor_json(e, True))
            elif e.get("type")=="badge": sensors.extend(status_sensors(e))
        diy.append({"img": f"generated/{fn}", "sensor": sensors, "type": 5})
    O.write_text(json.dumps({"diy":diy,"mianban":list(range(1,len(diy)+1)),"setup":{"refresh":1,"switchTime":str(layout.get("switchTime",6))}}, ensure_ascii=False, indent=2))
    return {"ok":True,"version":"0.8.10","panels":len(diy)}

def activate():
    result=build(); stamp=time.strftime("%Y%m%d-%H%M%S")
    if M.exists(): shutil.copy2(M, B / f"monitor-before-activate-{stamp}.json")
    shutil.copy2(O, M); return result

if __name__ == "__main__":
    import sys; print(json.dumps(activate() if "--activate" in sys.argv else build()))


