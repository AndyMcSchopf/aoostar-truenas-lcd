"use strict";
window.AOOSTAR_LAYOUT={
 version:5,W:960,H:376,
 imageRect(iw,ih,mode,zoom,x,y){
  const b=mode==="cover"?Math.max(960/iw,376/ih):mode==="contain"?Math.min(960/iw,376/ih):1;
  const s=b*(Number(zoom)||1),w=iw*s,h=ih*s;
  return {w,h,left:(960-w)/2+(Number(x)||0),top:(376-h)/2+(Number(y)||0)};
 },
 systemElements(){return [
  {type:"header",text:"TrueNAS Scale / TrueSTARMax",x:18,y:14,w:924,h:42,accent:"orange"},
  {type:"card",text:"CPU",x:28,y:72,w:280,h:226,accent:"orange"},
  {type:"sensor",label:"cpu_usage_percent",title:"",x:48,y:108,size:36,unit:"%"},
  {type:"sensor",label:"temperature_cpu",title:"",x:190,y:111,size:30,unit:"C"},
  {type:"bar",label:"cpu_usage_percent",x:48,y:157,w:235,h:12,max:100,accent:"orange"},
  {type:"sparkline",label:"cpu_usage_percent",x:48,y:188,w:235,h:82,auto:true,accent:"orange"},
  {type:"card",text:"RAM",x:330,y:72,w:280,h:226,accent:"violet"},
  {type:"sensor",label:"mem_usage_percent",title:"",x:350,y:108,size:36,unit:"%"},
  {type:"sensor",label:"temperature_memory",title:"",x:492,y:111,size:30,unit:"C"},
  {type:"bar",label:"mem_usage_percent",x:350,y:157,w:235,h:12,max:100,accent:"violet"},
  {type:"sparkline",label:"mem_usage_percent",x:350,y:188,w:235,h:82,max:100,accent:"violet"},
  {type:"card",text:"NETZWERK",x:632,y:72,w:300,h:150,accent:"blue"},
  {type:"sensor",label:"truenas_net_down",title:"DOWN",x:650,y:112,size:27,unit:""},
  {type:"sensor",label:"truenas_net_up",title:"UP",x:790,y:112,size:27,unit:""},
  {type:"sparkline",label:"truenas_net_down_bytes_sec",x:650,y:158,w:258,h:45,auto:true,accent:"blue"},
  {type:"card",text:"STATUS",x:632,y:236,w:300,h:94,accent:"amber"},
  {type:"badge",label:"truenas_system_status",x:650,y:273,w:105,h:34},
  {type:"sensor",label:"truenas_uptime",title:"",x:775,y:274,size:20,unit:""}
 ]},
 storageElements(){return [
  {type:"header",text:"SPEICHER / ZFS 02",x:18,y:14,w:924,h:42,accent:"amber"},
  {type:"pool",index:0,x:28,y:72,w:440,h:126,accent:"orange"},
  {type:"pool",index:1,x:492,y:72,w:440,h:126,accent:"blue"},
  {type:"pool",index:2,x:28,y:218,w:440,h:126,accent:"violet"},
  {type:"pool",index:3,x:492,y:218,w:440,h:126,accent:"pink"}
 ]},
 truenasElements(){return [
  {type:"header",text:"TRUENAS CORE SERVICES 03",x:18,y:14,w:924,h:42,accent:"orange"},
  {type:"card",text:"APPS",x:28,y:72,w:300,h:230,accent:"violet"},
  {type:"sensor",label:"truenas_apps_running",title:"AKTIV",x:48,y:118,size:34,unit:""},
  {type:"sensor",label:"truenas_apps_stopped",title:"STOPP",x:185,y:118,size:30,unit:""},
  {type:"sensor",label:"truenas_apps_updates",title:"UPDATES",x:48,y:205,size:32,unit:""},
  {type:"sensor",label:"truenas_apps_crashed",title:"FEHLER",x:185,y:205,size:30,unit:""},
  {type:"card",text:"ZFS / SYSTEM",x:350,y:72,w:582,h:230,accent:"orange"},
  {type:"sensor",label:"truenas_pools_healthy_de",title:"POOLS",x:375,y:122,size:31,unit:""},
  {type:"badge",label:"truenas_system_status",x:785,y:105,w:120,h:36},
  {type:"sensor",label:"truenas_version",title:"VERSION",x:375,y:218,size:23,unit:""},
  {type:"sensor",label:"truenas_uptime",title:"UPTIME",x:650,y:218,size:22,unit:""}
 ]},
 migrate(L){
  L.panels=L.panels||[];
  if((Number(L.schemaVersion)||0)<5){
   const sys=L.panels.find(p=>/system/i.test(p.name||""));
   const sto=L.panels.find(p=>/speicher|zfs/i.test(p.name||""));
   const tru=L.panels.find(p=>/^truenas$/i.test(p.name||""));
   if(sys){sys.elements=this.systemElements();sys.background="";}
   if(sto){sto.elements=this.storageElements();sto.background="";}
   if(tru){tru.elements=this.truenasElements();tru.background="";}
  }
  for(const p of L.panels){p.image=Object.assign({mode:"cover",x:0,y:0,zoom:1},p.image||{});p.elements=p.elements||[];}
  L.schemaVersion=5;L.appVersion="0.7.11.1";return L;
 }
};
/* v0.8.4 shared LCD-first cover geometry.
   Equivalent to Pillow ImageOps.fit/cover semantics:
   scale to cover destination, center overflow, then apply editor x/y in output pixels. */
function lcdCoverRect(sw, sh, dw, dh, zoom, ox, oy) {
  sw = Math.max(1, Number(sw)||1); sh = Math.max(1, Number(sh)||1);
  dw = Math.max(1, Number(dw)||1); dh = Math.max(1, Number(dh)||1);
  zoom = Math.max(0.01, Number(zoom)||1);
  const scale = Math.max(dw/sw, dh/sh) * zoom;
  const rw = sw*scale, rh = sh*scale;
  return {x:(dw-rw)/2 + (Number(ox)||0), y:(dh-rh)/2 + (Number(oy)||0), w:rw, h:rh, scale};
}