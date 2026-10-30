"""Pós-processa o index.html gerado pelo pygbag: tela responsiva + ponte do ranking online."""
import re
import shutil
import sys
from pathlib import Path

web = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
idx = web / "index.html"
html = idx.read_text(encoding="utf-8")

CONFIG = 'window.AGUIA_CONFIG = { supabaseUrl: "", supabaseKey: "", table: "ranking" };\n'
cfg = web / "ranking-config.js"
if not cfg.exists():
    cfg.write_text(CONFIG, encoding="utf-8")

INJECT = """
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="theme-color" content="#08101f">
<style>
html,body{margin:0;height:100%;background:#08101f;overflow:hidden;overscroll-behavior:none;touch-action:none;
-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
canvas#canvas,canvas.emscripten{position:fixed!important;inset:0;margin:auto!important;border:0!important;
width:min(100vw,calc(100dvh*450/800))!important;height:min(100dvh,calc(100vw*800/450))!important;touch-action:none}
</style>
<script src="ranking-config.js"></script>
<script>
(function(){
  var C=window.AGUIA_CONFIG||{}, base=(C.supabaseUrl||"").replace(/\\/$/,""), key=C.supabaseKey||"", t=C.table||"ranking";
  var H={apikey:key,Authorization:"Bearer "+key};
  window.aguiaTop="[]";
  window.aguiaRefresh=function(){
    if(!base||!key)return;
    fetch(base+"/rest/v1/"+t+"?select=name,score,level&order=score.desc&limit=10",{headers:H})
      .then(function(r){return r.ok?r.json():[]}).then(function(j){window.aguiaTop=JSON.stringify(j)}).catch(function(){});
  };
  window.aguiaSubmit=function(n,s,l){
    if(!base||!key)return;
    fetch(base+"/rest/v1/"+t,{method:"POST",headers:Object.assign({"Content-Type":"application/json",Prefer:"return=minimal"},H),
      body:JSON.stringify({name:String(n).slice(0,12),score:s|0,level:l|0})}).then(window.aguiaRefresh).catch(function(){});
  };
  document.addEventListener("contextmenu",function(e){e.preventDefault()});
})();
</script>
"""
html = re.sub(r"<meta[^>]+name=[\"']viewport[\"'][^>]*>", "", html, flags=re.I)
html = re.sub(r"<title>.*?</title>", "<title>Águia — Voo dos 20 Céus</title>", html, flags=re.S | re.I)
html = html.replace("</head>", INJECT + "</head>", 1) if "</head>" in html else INJECT + html
idx.write_text(html, encoding="utf-8")
print("index.html ajustado; configure o ranking em", cfg)
