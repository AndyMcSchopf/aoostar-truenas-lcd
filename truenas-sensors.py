#!/usr/bin/env python3
import json, os, socket, ssl, time
from pathlib import Path
from websocket import create_connection

OUT = Path('/app/cfg/sensors/truenas.txt')
INTERVAL = int(os.getenv('REFRESH_SECONDS', '5'))
HOST = os.getenv('TRUENAS_HOST', '127.0.0.1')
WS_URL = os.getenv('TRUENAS_WS_URL', f'wss://{HOST}/api/current')
USER = os.getenv('TRUENAS_API_USER', '')
KEY = os.getenv('TRUENAS_API_KEY', '')
VERIFY_TLS = os.getenv('TRUENAS_VERIFY_TLS', 'false').lower() in ('1','true','yes')
NET_IFACE = os.getenv('TRUENAS_NET_IFACE', '')

seq = 0
def rpc(ws, method, params=None):
    global seq
    seq += 1
    ws.send(json.dumps({'jsonrpc':'2.0','id':seq,'method':method,'params':params or []}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get('id') == seq:
            if 'error' in msg: raise RuntimeError(str(msg['error']))
            return msg.get('result')

def api_snapshot():
    if not KEY: return {}
    opts = {} if VERIFY_TLS else {'cert_reqs': ssl.CERT_NONE}
    ws = create_connection(WS_URL, timeout=5, sslopt=opts)
    try:
        login = rpc(ws, 'auth.login_ex', [{'mechanism':'API_KEY_PLAIN','username':USER,'api_key':KEY,'login_options':{'user_info':False}}])
        if not isinstance(login, dict) or login.get('response_type') != 'SUCCESS':
            raise RuntimeError('API authentication failed')
        system = rpc(ws, 'system.info') or {}
        pools = rpc(ws, 'pool.query') or []
        apps = rpc(ws, 'app.query') or []
        return {'system':system, 'pools':pools, 'apps':apps}
    finally:
        ws.close()

def default_iface():
    if NET_IFACE: return NET_IFACE
    try:
        for name in os.listdir('/sys/class/net'):
            if name != 'lo' and Path(f'/sys/class/net/{name}/operstate').read_text().strip() == 'up': return name
    except Exception: pass
    return ''

def net_bytes(iface):
    try:
        base=Path('/sys/class/net')/iface/'statistics'
        return int((base/'rx_bytes').read_text()), int((base/'tx_bytes').read_text())
    except Exception: return 0,0

def fmt_rate(v):
    if v >= 1024**2: return f'{v/1024**2:.1f}M/s'
    if v >= 1024: return f'{v/1024:.0f}K/s'
    return f'{v}B/s'

def local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('1.1.1.1',80)); ip=s.getsockname()[0]; s.close(); return ip
    except Exception: return 'n/a'

def write(vals):
    tmp=OUT.with_suffix('.tmp')
    tmp.write_text(''.join(f'{k}: {v}\n' for k,v in vals.items()), encoding='utf-8')
    tmp.replace(OUT)

iface=default_iface(); prev_rx,prev_tx=net_bytes(iface); prev_t=time.monotonic()
while True:
    time.sleep(INTERVAL)
    now=time.monotonic(); rx,tx=net_bytes(iface); dt=max(now-prev_t,0.1)
    vals={
      'truenas_ip': local_ip(),
      'truenas_net_down': 'Down:'+fmt_rate(max(0,int((rx-prev_rx)/dt))),
      'truenas_net_up': 'Up:'+fmt_rate(max(0,int((tx-prev_tx)/dt))),
      'truenas_iface': iface or 'n/a',
      'truenas_api': 'disabled' if not KEY else 'error',
    }
    prev_rx,prev_tx,prev_t=rx,tx,now
    try:
        snap=api_snapshot()
        if snap:
            vals['truenas_api']='ok'
            sys=snap['system']; pools=snap['pools']; apps=snap['apps']
            vals['truenas_hostname']=sys.get('hostname','n/a')
            vals['truenas_version']=sys.get('version','n/a')
            vals['truenas_uptime']=sys.get('uptime','n/a')
            vals['truenas_apps']=f"Apps:{sum(1 for a in apps if a.get('state')=='RUNNING')}/{len(apps)}"
            vals['truenas_pool_count']=str(len(pools))
            vals['truenas_pool_health']=' '.join(f"{p.get('name')}:{p.get('status')}" for p in pools) or 'no pools'
            scans=[]
            for p in pools:
                scan=p.get('scan') or {}
                if scan and scan.get('state'):
                    scans.append(f"{p.get('name')}:{scan.get('state')} {scan.get('percentage') or 0}%")
            vals['truenas_scrub']=' '.join(scans) if scans else 'idle'
            for i,p in enumerate(pools[:8]):
                vals[f'truenas_pool_{i}_name']=p.get('name','')
                vals[f'truenas_pool_{i}_status']=p.get('status','')
    except Exception as e:
        vals['truenas_api']='error'
        vals['truenas_api_error']=str(e).replace('\n',' ')[:100]
    write(vals)
