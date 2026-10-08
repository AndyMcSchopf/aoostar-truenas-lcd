from pathlib import Path
import ast
s=Path('/app/lcd_generator.py').read_text()
ast.parse(s)
assert 'd.rounded_rectangle((x,y,x+w,y+30),radius=15' in s
assert 'cap_x=max(x+100' in s
assert 'pct_bbox=d.textbbox' in s
assert 'capacityFormat' in s and 'capacitySize' in s
print('v0.8.11 pool renderer regression: OK')
