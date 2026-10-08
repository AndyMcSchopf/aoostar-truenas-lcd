#!/usr/bin/env python3
from pathlib import Path
import ast

g = Path('/app/lcd_generator.py').read_text(encoding='utf-8')
ast.parse(g)

# v0.8.9.1 originally asserted the old formula:
# y + status_size + gap. v0.8.10 intentionally replaced that with
# line boxes based on rendered font size. Verify the current invariant instead.
for token in (
    'gap=int(e.get("detailGap",6))',
    'main_h=max(18, round(status_size*1.35))',
    'detail_h=max(18, round(detail_size*1.35))',
    'detail_y=y+main_h+gap',
    'remaining=max(18,total_h-main_h-gap)',
):
    assert token in g, token

# Geometry sanity check.
def boxes(y, total_h, status_size, detail_size, gap):
    main_h=max(18, round(status_size*1.35))
    detail_h=max(18, round(detail_size*1.35))
    detail_y=y+main_h+gap
    remaining=max(18,total_h-main_h-gap)
    return main_h, detail_y, min(remaining,detail_h)

mh, dy, dh = boxes(100, 100, 32, 20, 8)
assert mh == 43
assert dy == 151
assert dh == 27
print('v0.8.9.1 compatibility test on v0.8.10 line-box geometry: OK')
