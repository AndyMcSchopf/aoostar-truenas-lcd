from pathlib import Path
import ast
s = Path('/app/lcd_generator.py').read_text(encoding='utf-8')
ast.parse(s)
# v0.8.12 replaces the old fixed 30px pool header with responsive geometry.
assert 'head=max(30' in s or 'head = max(30' in s, 'responsive header height missing'
assert 'd.rounded_rectangle((x,y,x+w,y+head),radius=15' in s, 'rounded responsive header missing'
assert 'capacityFormat' in s and 'capacitySize' in s, 'pool capacity configuration missing'
assert 'bar_top+bar_h+12<=hh' in s, 'pool overflow guard missing'
print('v0.8.11 compatibility on v0.8.12 responsive pool renderer: OK')
