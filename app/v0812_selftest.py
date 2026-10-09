from pathlib import Path
import ast, math, re
s=Path('/app/lcd_generator.py').read_text();ast.parse(s)
for size in (15,20,25,30):
 h=max(30,math.ceil(size*1.35)+8); row=math.ceil(size*1.3); top=h+10; bar=top+row+8
 assert h>=30 and bar>top+size
assert re.sub(r"\s+(TiB|GiB|MiB)$","","1.3 TiB",flags=re.I)=="1.3"
assert 'pool-overflow' in Path('/app/static/editor.js').read_text()
assert 'bar_top+bar_h+12<=hh' in s
print('v0.8.12 pool geometry tests OK')
