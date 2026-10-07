#!/usr/bin/env python3
from pathlib import Path
e=Path("/app/static/editor.js").read_text();g=Path("/app/lcd_generator.py").read_text()
for t in ("detailGap","Kapazität Größe","capacityFormat","Poolname Größe","Prozent Größe","poolobj"): assert t in e,t
for t in ("detailGap","capacitySize","percentSize","nameSize","capacityFormat"): assert t in g,t
print("v0.8.9 selftest: OK")
