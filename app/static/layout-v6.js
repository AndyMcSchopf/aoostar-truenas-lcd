"use strict";
(function(){
 const B=window.AOOSTAR_LAYOUT, old=B.migrate.bind(B);
 B.version=6;
 B.migrate=function(L){
  L=old(L);
  if((Number(L.schemaVersion)||0)<6){
   const p=(L.panels||[]).find(x=>/^BILD$/i.test(x.name||""));
   if(p)p.elements=(p.elements||[]).filter(e=>
    !(e.type==="header"&&e.text==="TrueSTARMax / Working Elf") &&
    !(e.type==="sensor"&&e.label==="truenas_model"));
  }
  for(const p of (L.panels||[]))for(const e of (p.elements||[])){
   if(e.type==="badge"){e.size=e.size||22;e.lcdOffsetY=8;}
   if(e.label==="truenas_uptime")e.lcdOffsetY=8;
  }
  L.schemaVersion=6;L.appVersion="0.7.12";return L;
 };
})();