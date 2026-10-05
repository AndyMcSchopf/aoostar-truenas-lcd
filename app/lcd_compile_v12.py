from pathlib import Path
import re, shutil
def compact_uptime(raw):
    s=str(raw or "").strip()
    m=re.match(r"(?:(\d+)\s+days?,\s*)?(\d+):(\d+):",s)
    if not m:return s
    d=int(m.group(1) or 0);h=int(m.group(2));mi=int(m.group(3))
    return f"{d}d {h}h" if d else f"{h}h {mi:02d}m"
def clean_generated(cfg):
    p=Path(cfg)/"generated"
    if p.exists():shutil.rmtree(p)
    p.mkdir(parents=True,exist_ok=True)
def lcd_sensor(e,values):
    label=e.get("label","");val=values.get(label,"")
    if label=="truenas_uptime":val=compact_uptime(val)
    size=int(e.get("size",22 if e.get("type")=="badge" else 24))
    return {"decimalDigits":-1,"direction":1,"fontColor":-1,"fontFamily":"HarmonyOS_Sans_SC_Bold",
    "fontSize":size,"fontWeight":"bold","height":0,"integerDigits":-1,"label":label,
    "maxAngle":180,"maxValue":100,"minAngle":0,"minValue":0,"mode":1,"name":"",
    "pic":"","textAlign":"center","textDirection":0,"type":1,"unit":e.get("unit",""),
    "value":str(val),"width":0,"x":int(e.get("lcdX",e.get("x",0))),"xz_x":0,"xz_y":0,
    "y":int(e.get("lcdY",e.get("y",0)))+int(e.get("lcdOffsetY",8))}
def write_report(path,panels):
    Path(path).write_text("\n".join(panels),encoding="utf-8")
