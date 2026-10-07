#!/usr/bin/env python3
from pathlib import Path
import ast

g=Path("/app/lcd_generator.py").read_text(encoding="utf-8")
ast.parse(g)
for t in ("detailGap","capacitySize","percentSize","nameSize","capacityFormat"):
    assert t in g, t

# Verify the status detail geometry uses the configured gap in both y and h.
assert 'gap=int(e.get("detailGap",6))' in g
assert '+int(e.get("size",22))+gap' in g
assert '-int(e.get("size",22))-gap' in g
print("v0.8.9.1 status gap regression test: OK")
