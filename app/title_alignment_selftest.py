#!/usr/bin/env python3
from pathlib import Path
e=Path("/app/static/editor.js").read_text()
g=Path("/app/lcd_generator.py").read_text()
assert 'display:block;width:100%' in e
assert 'text-align:${ta}' in e
assert 'e.get("titleAlign", "left")' in g
assert 'align == "center"' in g
assert 'align == "right"' in g
assert 'd.textbbox' in g
print("title alignment selftest: OK")
