"use strict";
(function(){
 const previous=window.html;
 function esc(s){return String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
 function pool(z,i){
  const n=Number(z.index)||0,k=`truenas_pool_${n}_`,pct=parseFloat(V[k+"used_percent"]||0),name=V[k+"name"]||`POOL ${n+1}`,st=V[k+"status"]||"",used=V[k+"used"]||"",size=V[k+"size"]||"";
  const a=C(z.accent),warn=pct>=90?"#CC6666":pct>=75?"#FFCC66":a;
  return `<div class="obj card ${i===ei?"selected":""}" data-i="${i}" style="left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px;overflow:hidden"><div class="cardhead" style="height:34px;padding:8px 14px;background:${warn};font-size:17px">${esc(name)} - ${esc(st)}</div><div style="padding:8px 16px;display:grid;grid-template-columns:110px 1fr;align-items:center;gap:8px"><b style="font-size:34px;line-height:1">${pct.toFixed(0)}%</b><b style="font-size:20px">${esc(used)} / ${esc(size)}</b><div class="bar" style="grid-column:1/-1;height:13px"><div style="height:100%;width:${Math.max(0,Math.min(100,pct))}%;background:${warn}"></div></div></div></div>`;
 }
 function spark(z,i,a){
  const v=(H[z.label]||[]).slice(-60),w=z.w,h=z.h;
  if(v.length<2)return `<div class="obj ${i===ei?"selected":""}" data-i="${i}" style="left:${z.x}px;top:${z.y}px;width:${w}px;height:${h}px;overflow:hidden"></div>`;
  const nums=v.map(x=>Number(x.value??x)||0),mx=z.auto?Math.max(1,...nums)*1.15:(z.max||Math.max(...nums,1));
  const pts=nums.map((n,k)=>`${k/(nums.length-1)*w},${h-Math.max(0,Math.min(1,n/mx))*h}`).join(" "),area=`0,${h} ${pts} ${w},${h}`;
  return `<svg class="obj ${i===ei?"selected":""}" data-i="${i}" style="left:${z.x}px;top:${z.y}px;overflow:hidden" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><defs><clipPath id="clip${i}"><rect width="${w}" height="${h}"/></clipPath></defs><g clip-path="url(#clip${i})"><polygon points="${area}" fill="${a}" fill-opacity=".07"/><polyline points="${pts}" fill="none" stroke="${a}" stroke-width="3"/></g></svg>`;
 }
 window.html=function(z,i,t){/* Pool rendering belongs to editor.js (responsive renderer). */if(z.type==="sparkline")return spark(z,i,C(z.accent));return previous(z,i,t);};
})();