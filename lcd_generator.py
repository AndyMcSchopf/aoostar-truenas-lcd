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
    d.text((x, y), title, font=font(label_size), fill=text_rgb(e.get("titleColor","muted"),"muted"))

def panel(p, i, values, history):
    im = Image.new("RGBA", (W, H), rgb(T["bg"]) + (255,))
    bg = p.get("background"); m = p.get("image", {})
    if bg and (C / "images" / bg).exists():
        src = Image.open(C / "images" / bg).convert("RGBA")
        rw, rh, ox, oy = image_rect(src.width, src.height, m.get("mode", "cover"), m.get("zoom", 1), m.get("x", 0), m.get("y", 0))
        src = src.resize((round(rw), round(rh))); im.alpha_composite(src, (round(ox), round(oy)))
    d = ImageDraw.Draw(im)
    native = (i in (0, 2, 3))  # v0.8.1: SYSTEM, TRUENAS and BILD
    for e in p.get("elements", []):
        if i == 3 and ((e.get("type") == "header" and e.get("text") == "TrueSTARMax / Working Elf") or (e.get("type") == "sensor" and e.get("label") == "truenas_model")):
            continue
        q = e.get("type"); a = T.get(e.get("accent", "orange"), T["orange"])
        x, y, w, hh = int(e.get("x",0)), int(e.get("y",0)), int(e.get("w",0)), int(e.get("h",0))
        if q == "header":
            d.rounded_rectangle((x,y,x+w,y+hh), radius=min(20,max(1,hh//2)), fill=rgb(a)); d.text((x+16,y+8),e.get("text",""),font=font(17),fill=(10,10,10))
        elif q == "card":
            radius = min(20, max(1, hh // 2))
            d.rounded_rectangle((x,y,x+w,y+hh),radius=radius,fill=rgb(T["panel"]))
            # Rounded top corners, square lower edge: same visual contract as editor cardhead.
            d.rounded_rectangle((x,y,x+w,y+30),radius=min(radius,15),fill=rgb(a))
            d.rectangle((x,y+15,x+w,y+30),fill=rgb(a))
            d.text((x+14,y+5),e.get("text",""),font=font(int(e.get("size",15))),fill=text_rgb(e.get("textColor","auto")))
        elif q == "pool":
            n=int(e.get("index",0)); k=f"truenas_pool_{n}_"; pct=float(values.get(k+"used_percent",0) or 0); col="#CC6666" if pct>=90 else "#FFCC66" if pct>=75 else a
            d.rounded_rectangle((x,y,x+w,y+hh),radius=20,fill=rgb(T["panel"])); d.rectangle((x,y,x+w,y+30),fill=rgb(col)); d.text((x+14,y+5),f'{values.get(k+"name","POOL")} · {values.get(k+"status","")}',font=font(13),fill=(10,10,10)); d.text((x+18,y+42),f"{pct:.0f}%",font=font(25),fill=rgb(T["text"])); d.text((x+100,y+49),f'{values.get(k+"used","")} / {values.get(k+"size","")}',font=font(12),fill=text_rgb(e.get("titleColor","muted"),"muted")); d.rounded_rectangle((x+18,y+88,x+w-18,y+99),5,fill=(45,49,57)); d.rounded_rectangle((x+18,y+88,x+18+(w-36)*pct/100,y+99),5,fill=rgb(col))
        elif q == "sparkline": spark(im,(x,y,w,hh),history.get(e.get("label"),[]),a,e.get("max"))
        elif q == "text": d.text((x,y),e.get("text",""),font=font(e.get("size",24)),fill=rgb(T["text"]))
        elif q in ("sensor", "badge") and native:
            draw_static_label(d, e)
    fn = f"panel_{i+1}.png"; im.convert("RGB").save(G / fn); return fn

def build():
    clean_generated()
    layout = json.loads((C / "layout-v07.json").read_text()); values = readvals(); history = hist(); diy = []
    for i, p in enumerate(layout.get("panels", [])):
        fn = panel(p, i, values, history)
        native = (i in (0, 2, 3))
        elements = [e for e in p.get("elements", []) if not (i == 3 and ((e.get("type") == "header" and e.get("text") == "TrueSTARMax / Working Elf") or (e.get("type") == "sensor" and e.get("label") == "truenas_model")))]
        sensors = [sensor_json(e, native) for e in elements if e.get("type") in (("sensor","badge") if native else ("sensor",))]
        diy.append({"img": f"generated/{fn}", "sensor": sensors, "type": 5})
    O.write_text(json.dumps({"diy":diy,"mianban":list(range(1,len(diy)+1)),"setup":{"refresh":1,"switchTime":str(layout.get("switchTime",6))}}, ensure_ascii=False, indent=2))
    return {"ok":True,"version":"0.8.5.4","nativePanels":["SYSTEM","TRUENAS","BILD"],"panels":len(diy)}

def activate():
    result=build(); stamp=time.strftime("%Y%m%d-%H%M%S")
    if M.exists(): shutil.copy2(M, B / f"monitor-before-activate-{stamp}.json")
    shutil.copy2(O, M); return result

if __name__ == "__main__":
    import sys; print(json.dumps(activate() if "--activate" in sys.argv else build()))def text_rgb(name, default="white"):
    if not name or name in ("auto","white"): return rgb(T["text"])
    if name=="muted": return rgb(T["muted"])
    if name=="green": return (102,204,153)
    return rgb(T.get(name, T["text"]))


