#!/usr/bin/env python3
import re
used="48.3 TiB"
total="98.2 TiB"
short_used=re.sub(r"\s+(TiB|GiB|MiB)$","",used)
cap=f"{short_used} / {total}"
assert cap=="48.3 / 98.2 TiB", cap
print("v0.8.9.2 pool compact runtime test: OK")
