import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srv import serve
from playwright.sync_api import sync_playwright
fails=[]
def check(c,m):
    print(("  ok  " if c else "  FALHA ")+m)
    if not c: fails.append(m)
def st(pg,s,t=8000): pg.wait_for_function(f"Aguia.app.state==='{s}'", timeout=t)
SB_URL="https://demo-project.supabase.co"; SB_KEY="k"*40
with sync_playwright() as p, serve() as URL:
    b=p.chromium.launch(); errs=[]
    def newpage(init=None, config=None, **kw):
        ctx=b.new_context(viewport={"width":390,"height":844}, has_touch=True, is_mobile=True, **kw); pg=ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        if init: pg.add_init_script(init)
        if config: pg.route("**/ranking-config.js", lambda r,q: r.fulfill(content_type="application/javascript", body=config))
        return ctx,pg
    print("# Troca de nível, vitória e visibilidade")
    ctx,pg=newpage(); pg.goto(URL); st(pg,"menu"); pg.click("#btnNew"); st(pg,"play"); pg.wait_for_timeout(300)
    pg.evaluate("(()=>{const w=Aguia.app.world; w.lt=29.98; w.score=500;})()"); pg.wait_for_function("Aguia.app.world.level===2", timeout=3000)
    check("nível 2" in pg.inner_text("#banner").lower() and "mais rápido" in pg.inner_text("#banner").lower(), "faixa do nível 2 aparece: "+pg.inner_text("#banner").replace("\n"," | "))
    check("2/20" in pg.inner_text("#levelPill"), "HUD mostra nível 2/20")
    check(json.loads(pg.evaluate("localStorage.getItem('aguia.save.v1')"))["level"]==2, "troca de nível grava o autosave")
    check(pg.evaluate("Aguia.app.world.score")==700, "bônus do nível 1 somado (500 + 200)")
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); document.dispatchEvent(new Event('visibilitychange'))")
    st(pg,"pause",2000); check(True,"aba escondida pausa o jogo")
    pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false})"); pg.click("#btnResume"); st(pg,"play")
    pg.evaluate("(()=>{const w=Aguia.app.world; w.level=20; w.c=Aguia.Game.cfg(20); w.lt=29.98; w.score=40000;})()"); st(pg,"over",3000)
    check("vitória" in pg.inner_text("#overTitle").lower(), "zerar o nível 20 mostra VITÓRIA")
    check(pg.inner_text("#overScore").replace(".","")=="42000"+"" or int(pg.inner_text("#overScore").replace(".",""))==40000+200*20+2000, "pontuação final = 40.000 + 4.000 + 2.000: "+pg.inner_text("#overScore"))
    ctx.close()

    print("# Ranking online (Supabase simulado)")
    cfg=f"window.AGUIA_CONFIG={{supabaseUrl:'{SB_URL}',supabaseKey:'{SB_KEY}',table:'ranking'}};"
    ctx,pg=newpage(config=cfg); posted=[]
    def sb(route, req):
        if req.method=="GET":
            assert "order=score.desc" in req.url and "limit=10" in req.url
            route.fulfill(status=200, content_type="application/json", headers={"access-control-allow-origin":"*"}, body=json.dumps([{"name":"Ana","score":9000,"level":9},{"name":"Bia","score":5000,"level":6}]))
        elif req.method=="POST":
            posted.append(json.loads(req.post_data)); route.fulfill(status=201, headers={"access-control-allow-origin":"*"}, body="")
        else: route.fulfill(status=204, headers={"access-control-allow-origin":"*","access-control-allow-headers":"apikey,authorization,content-type,prefer","access-control-allow-methods":"GET,POST,OPTIONS"})
    pg.route(SB_URL+"/**", sb)
    pg.goto(URL); st(pg,"menu"); pg.tap("#btnRank"); pg.wait_for_function("document.querySelectorAll('#rankRows li').length===2", timeout=5000)
    check(pg.locator("#rankTabs").is_visible() and "todos os jogadores" in pg.inner_text("#rankSrc"), "abas Global/Aparelho e origem online: "+pg.inner_text("#rankSrc"))
    check("Ana" in pg.inner_text("#rankRows"), "lista vem do servidor")
    pg.tap("#tabLocal"); pg.wait_for_timeout(200); check("Nenhuma" in pg.inner_text("#rankRows"), "aba 'Neste aparelho' mostra só o local")
    pg.tap("#sc-rank [data-back]"); pg.tap("#btnNew"); st(pg,"play")
    pg.evaluate("(()=>{const w=Aguia.app.world; w.score=3210; w.inv=0; w.hp=1; w.hurt();})()"); st(pg,"over")
    pg.fill("#nameIn","Zé"); pg.tap("#btnSave"); pg.wait_for_function("document.getElementById('overMsg').textContent.includes('online')", timeout=6000)
    check(posted and posted[0]=={"name":"Zé","score":3210,"level":1}, f"POST enviado ao servidor: {posted}")
    check("enviado ao ranking online" in pg.inner_text("#overMsg"), "mensagem confirma o envio")
    ctx.close()

    print("# Ranking online fora do ar")
    ctx,pg=newpage(config=cfg); pg.route(SB_URL+"/**", lambda r,q: r.abort())
    pg.goto(URL); st(pg,"menu"); pg.tap("#btnRank"); pg.wait_for_function("document.getElementById('rankSrc').textContent.includes('indisponível')", timeout=9000)
    check(True,"falha do servidor mostra aviso e cai para o ranking local")
    pg.tap("#sc-rank [data-back]"); pg.tap("#btnNew"); st(pg,"play"); pg.evaluate("(()=>{const w=Aguia.app.world; w.score=50; w.inv=0; w.hp=1; w.hurt();})()"); st(pg,"over")
    pg.tap("#btnSave"); pg.wait_for_function("document.getElementById('overMsg').textContent.includes('indisponível')", timeout=9000)
    check("Nº 1 neste aparelho" in pg.inner_text("#overMsg"), "pontuação fica salva localmente mesmo sem o servidor: "+pg.inner_text("#overMsg"))
    ctx.close()

    print("# Banco do Claude (artifact simulado)")
    fake="""window.claude={use:async(n)=>n==='db'?{collection:(c)=>({
      orderBy:()=>({limit:()=>({get:async()=>({docs:[{data:()=>({name:'Rui',score:777,level:3})}]})})}),
      add:async(d)=>{(window.__added=window.__added||[]).push([c,d]);return {}}})}:null};"""
    ctx,pg=newpage(init=fake); pg.goto(URL); st(pg,"menu"); pg.tap("#btnRank"); pg.wait_for_function("document.querySelectorAll('#rankRows li').length===1", timeout=5000)
    check("Rui" in pg.inner_text("#rankRows") and "quem tem acesso" in pg.inner_text("#rankSrc"), "lê o ranking do banco do artifact")
    pg.tap("#sc-rank [data-back]"); pg.tap("#btnNew"); st(pg,"play"); pg.evaluate("(()=>{const w=Aguia.app.world; w.score=99; w.inv=0; w.hp=1; w.hurt();})()"); st(pg,"over")
    pg.tap("#btnSave"); pg.wait_for_function("window.__added&&window.__added.length", timeout=5000)
    a=pg.evaluate("window.__added[0]"); check(a[0]=="ranking" and a[1]["score"]==99 and "ts" in a[1], f"grava no banco do artifact: {a}")
    ctx.close()

    print("# Armazenamento bloqueado")
    ctx,pg=newpage(init="Object.defineProperty(window,'localStorage',{get(){throw new Error('bloqueado')}});")
    pg.goto(URL); st(pg,"menu"); pg.tap("#btnNew"); st(pg,"play"); pg.wait_for_timeout(800)
    pg.evaluate("(()=>{const w=Aguia.app.world; w.score=10; w.inv=0; w.hp=1; w.hurt();})()"); st(pg,"over"); pg.tap("#btnSave"); pg.wait_for_function("document.getElementById('overMsg').textContent.includes('Nº')", timeout=5000)
    check(True,"sem localStorage o jogo e o ranking seguem funcionando (reserva em memória)")
    ctx.close(); b.close()
print("erros de página:", errs)
print("RESULTADO:", "tudo certo" if not fails and not errs else f"{len(fails)} falhas")
sys.exit(1 if fails or errs else 0)
