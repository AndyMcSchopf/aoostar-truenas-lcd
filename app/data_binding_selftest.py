#!/usr/bin/env python3
import json, os, subprocess, tempfile
from pathlib import Path

def main():
    root=Path(tempfile.mkdtemp(prefix='aoostar-v088-'))
    for d in ('sensors','backups','images'): (root/d).mkdir()
    layout={
      'schemaVersion':5,'appVersion':'0.8.8','theme':'lcars-orange','switchTime':6,
      'panels':[{'name':'BINDING','background':'','image':{'mode':'cover','x':0,'y':0,'zoom':1},'elements':[
        {'type':'bar','label':'temperature_cpu','x':20,'y':20,'w':200,'h':16,'min':20,'max':100,'accent':'orange'},
        {'type':'sparkline','label':'temperature_cpu','x':20,'y':50,'w':200,'h':60,'min':20,'max':100,'accent':'blue'},
        {'type':'badge','label':'truenas_system_status','detailLabel':'truenas_system_status_detail','x':250,'y':20,'w':300,'h':70,'size':22,'detailSize':12,'align':'center'}
      ]}]
    }
    (root/'layout-v07.json').write_text(json.dumps(layout))
    (root/'sensors/values.txt').write_text('temperature_cpu: 60\ntruenas_system_status: WARNUNG\ntruenas_system_status_detail: 1 App CRASHED\n')
    (root/'history.json').write_text(json.dumps({'temperature_cpu':[{'t':1,'value':40},{'t':2,'value':60}]}))
    env=dict(os.environ);env['AOOSTAR_CFG']=str(root)
    r=subprocess.run(['python3','/app/lcd_generator.py'],env=env,capture_output=True,text=True)
    assert r.returncode==0,(r.stdout,r.stderr)
    cfg=json.loads((root/'monitor.generated.json').read_text())
    assert len(cfg['diy'])==1
    sensors=cfg['diy'][0]['sensor']
    assert len(sensors)==2,sensors
    assert sensors[0]['label']=='truenas_system_status'
    assert sensors[1]['label']=='truenas_system_status_detail'
    assert sensors[0]['textAlign']=='center' and sensors[1]['textAlign']=='center'
    assert (root/'generated/panel_1.png').exists()
    print('AOOSTAR v0.8.8 data binding/status selftest OK')
if __name__=='__main__':main()
