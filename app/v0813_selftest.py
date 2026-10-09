from pathlib import Path
s=Path('/app/static/editor.js').read_text()
for prop in ('nameSize','percentSize','capacitySize','capacityFormat'):
 assert 'z.'+prop in s
for field in ('ipname','ippct','ipcap','ipfmt'):
 assert 'sourceId==="'+field+'"' in s
assert 'font-size:${ns}px' in s and 'font-size:${ps}px' in s and 'font-size:${cs}px' in s
assert 'renderCanvas();save()' in s
print('v0.8.13 pool inspector/renderer binding OK')
