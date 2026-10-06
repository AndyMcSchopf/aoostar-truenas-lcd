#!/usr/bin/env python3
import json, os, socket, ssl, time
from pathlib import Path
from websocket import create_connection

OUT = Path(os.environ.get('TRUENAS_SENSOR_OUT', '/app/cfg/sensors/truenas.txt'))
INTERVAL = max(1, int(os.getenv('REFRESH_SECONDS', '5')))
HOST = os.getenv('TRUENAS_HOST', '127.0.0.1')
WS_URL = os.getenv('TRUENAS_WS_URL', f'wss://{HOST}/api/current')
USER = os.getenv('TRUENAS_API_USER', '')
KEY = os.getenv('TRUENAS_API_KEY', '')

if KEY and not WS_URL.lower().startswith('wss://'):
    raise RuntimeError('TrueNAS API key authentication requires wss://')


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
            if 'error' in msg:
                raise RuntimeError(str(msg['error']))
            return msg.get('result')

def api_snapshot():
    if not KEY:
        return {}
    opts = {} if VERIFY_TLS else {'cert_reqs': ssl.CERT_NONE}
    ws = create_connection(WS_URL, timeout=8, sslopt=opts)
    try:
        login = rpc(ws, 'auth.login_ex', [{
            'mechanism':'API_KEY_PLAIN', 'username':USER, 'api_key':KEY,
            'login_options':{'user_info':False}
        }])
        if not isinstance(login, dict) or login.get('response_type') != 'SUCCESS':
            raise RuntimeError('API authentication failed')
        system = rpc(ws, 'system.info') or {}
        pools = rpc(ws, 'pool.query', [[], {}]) or []
        apps = rpc(ws, 'app.query', [[], {}]) or []
        return {'system':system, 'pools':pools, 'apps':apps}
    finally:
        ws.close()

def iface_usable(name):
    bad_prefixes = ('lo','veth','docker','br-','virbr','tap','tun','wg','tailscale','kube','cni')
    if not name or name.startswith(bad_prefixes):
        return False
    p = Path('/sys/class/net') / name
    try:
        return p.exists() and (p/'operstate').read_text().strip() in ('up','unknown')
    except Exception:
        return False

def default_route_iface():
    try:
        for line in Path('/proc/net/route').read_text().splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 4 and fields[1] == '00000000' and int(fields[3],16) & 2:
                if iface_usable(fields[0]):
                    return fields[0]
    except Exception:
        pass
    return ''

def default_iface():
    if NET_IFACE:
        return NET_IFACE
    route_iface = default_route_iface()
    if route_iface:
        return route_iface
    try:
        candidates=[]
        for name in os.listdir('/sys/class/net'):
            if iface_usable(name):
                rx,_ = net_bytes(name)
                candidates.append((rx,name))
        if candidates:
            return max(candidates)[1]
    except Exception:
        pass
    return ''

def net_bytes(iface):
    try:
        base=Path('/sys/class/net')/iface/'statistics'
        return int((base/'rx_bytes').read_text()), int((base/'tx_bytes').read_text())
    except Exception:
        return 0,0

def fmt_rate(v):
    v=max(0,int(v))
    if v >= 1024**3: return f'{v/1024**3:.1f} GB/s'
    if v >= 1024**2: return f'{v/1024**2:.1f} MB/s'
    if v >= 1024: return f'{v/1024:.1f} KB/s'
    return f'{v} B/s'

def fmt_bytes(v):
    try: v=int(v)
    except (TypeError,ValueError): return 'n/a'
    for unit in ('B','KiB','MiB','GiB','TiB','PiB'):
        if abs(v) < 1024 or unit == 'PiB': return f'{v:.0f} {unit}' if unit=='B' else f'{v:.1f} {unit}'
        v /= 1024.0

def local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('1.1.1.1',80)); ip=s.getsockname()[0]; s.close(); return ip
    except Exception: return 'n/a'

def scan_text(scan):
    if not scan: return 'idle'
    state=str(scan.get('state') or '').upper()
    function=str(scan.get('function') or 'scan').lower()
    pct=scan.get('percentage')
    if state in ('SCANNING','RUNNING') and pct is not None:
        return f'{function} {float(pct):.0f}%'
    if state:
        return f'{function} {state.lower()}'
    return 'idle'

def write(vals):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp=OUT.with_suffix('.tmp')
    tmp.write_text(''.join(f'{k}: {str(v).replace(chr(10)," ")}\n' for k,v in vals.items()), encoding='utf-8')
    tmp.replace(OUT)

iface=default_iface(); prev_rx,prev_tx=net_bytes(iface); prev_t=time.monotonic()
while True:
    time.sleep(INTERVAL)
    new_iface=default_iface()
    if new_iface != iface:
        iface=new_iface; prev_rx,prev_tx=net_bytes(iface); prev_t=time.monotonic()
    now=time.monotonic(); rx,tx=net_bytes(iface); dt=max(now-prev_t,0.1)
    down=max(0,int((rx-prev_rx)/dt)); up=max(0,int((tx-prev_tx)/dt))
    vals={
      'truenas_ip': local_ip(),
      'truenas_iface': iface or 'n/a',
      'truenas_net_down': fmt_rate(down),
      'truenas_net_up': fmt_rate(up),
      'truenas_net_down_bytes_sec': str(down),
      'truenas_net_up_bytes_sec': str(up),
      'truenas_api': 'deaktiviert' if not KEY else 'fehler',
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
            vals['truenas_model']=sys.get('model','n/a')
            running=sum(1 for a in apps if a.get('state')=='RUNNING')
            stopped=sum(1 for a in apps if a.get('state')=='STOPPED')
            crashed=sum(1 for a in apps if a.get('state')=='CRASHED')
            upgrades=sum(1 for a in apps if a.get('upgrade_available') or a.get('image_updates_available'))
            vals.update({
                'truenas_apps':f'{running}/{len(apps)}', 'truenas_apps_de':f'{running} von {len(apps)} aktiv', 'truenas_apps_running':str(running),
                'truenas_apps_stopped':str(stopped), 'truenas_apps_crashed':str(crashed),
                'truenas_apps_updates':str(upgrades), 'truenas_pool_count':str(len(pools)),
            })
            healthy=sum(1 for p in pools if p.get('healthy') is True or p.get('status')=='ONLINE')
            unhealthy_pools=max(0,len(pools)-healthy)
            if unhealthy_pools:
                health_state='KRITISCH'; health_detail=f'{unhealthy_pools} Pool(s) nicht ONLINE'
            elif crashed:
                health_state='WARNUNG'; health_detail=f'{crashed} App(s) CRASHED'
            elif upgrades:
                health_state='HINWEIS'; health_detail=f'{upgrades} Update(s) verfügbar'
            else:
                health_state='ONLINE'; health_detail='System, Pools und Apps ohne erkannten Fehler'
            vals['truenas_system_status']=health_state
            vals['truenas_system_status_detail']=health_detail
            vals['truenas_pools_healthy']=f'{healthy}/{len(pools)}'
            vals['truenas_pools_healthy_de']=f'{healthy} von {len(pools)} OK'
            vals['truenas_pool_health']=' '.join(f"{p.get('name')}:{p.get('status')}" for p in pools) or 'no pools'
            active=[]
            for i,p in enumerate(pools[:8]):
                name=p.get('name',''); status=p.get('status','n/a'); size=p.get('size'); alloc=p.get('allocated'); free=p.get('free')
                pct=round((float(alloc)/float(size))*100,1) if size and alloc is not None else 0
                scan=scan_text(p.get('scan'))
                vals[f'truenas_pool_{i}_name']=name
                vals[f'truenas_pool_{i}_status']=status
                vals[f'truenas_pool_{i}_healthy']='yes' if p.get('healthy') is True else ('yes' if status=='ONLINE' else 'no')
                vals[f'truenas_pool_{i}_used_percent']=str(pct)
                vals[f'truenas_pool_{i}_used']=fmt_bytes(alloc)
                vals[f'truenas_pool_{i}_free']=fmt_bytes(free)
                vals[f'truenas_pool_{i}_size']=fmt_bytes(size)
                vals[f'truenas_pool_{i}_scan']=scan
                if scan != 'idle': active.append(f'{name}:{scan}')
            vals['truenas_scrub']=' '.join(active) if active else 'idle'
            vals['truenas_scrub_de']=' '.join(active) if active else 'kein Scrub aktiv'
    except Exception as e:
        vals['truenas_api']='fehler'
        vals['truenas_system_status']='UNBEKANNT'
        vals['truenas_system_status_detail']='TrueNAS API nicht auswertbar'
        vals['truenas_api_error']=str(e).replace('\n',' ')[:160]
    write(vals)


