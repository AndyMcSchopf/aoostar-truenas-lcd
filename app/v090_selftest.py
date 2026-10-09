from pathlib import Path
import ast
s=Path('/app/lcd_generator.py').read_text();ast.parse(s)
assert '"durationSeconds"' in s and 'panel_config["durationSeconds"] = seconds' in s
assert '"switchTime":str(layout.get("switchTime",6))' in s
print('v0.9.0 generator timing contract OK')
