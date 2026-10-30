# Águia — Voo dos 20 Céus

Jogo 2D visto de cima, feito em HTML5 Canvas puro (sem framework, sem build obrigatório). Uma águia voa por
20 níveis desviando de montanhas, tempestades, gaviões e meteoros, coletando joias e caçando coelhos para
recuperar vida. Funciona em computador (mouse/teclado) e celular (toque), com salvamento automático e ranking.

## Colocar no ar

O site é **estático**: a pasta `web/` (ou o conteúdo do `aguia-site.zip`) é tudo o que precisa ser enviado.

1. Envie **todo o conteúdo** de `web/` para a raiz da sua hospedagem (o jogo abre em `index.html`).
   Serve qualquer uma: GitHub Pages, Netlify, Cloudflare Pages, Vercel ou hospedagem comum (cPanel/FTP).
2. Use **HTTPS** (as hospedagens acima já fornecem). É obrigatório para o ranking global funcionar a partir do
   navegador sem avisos de conteúdo misto.
3. (Opcional) Ative o ranking global — próxima seção. Sem isso o ranking funciona só no aparelho de cada jogador.

Se o jogo ficar numa subpasta (`seusite.com/aguia/`), nada precisa mudar: todos os caminhos são relativos.
Dica de cache: se você atualizar o jogo, mantenha `ranking-config.js` e `index.html` sem cache longo.

## Ranking global (Supabase, grátis)

1. Crie um projeto em <https://supabase.com>.
2. No **SQL Editor**, execute o conteúdo de `supabase.sql`. Ele cria a tabela `ranking`, liga a segurança por
   linha (leitura e envio liberados, edição e exclusão bloqueadas) e recusa pontuações impossíveis para o nível.
3. Em **Project Settings > API**, copie a *Project URL* e a chave **anon / public**.
4. Edite `ranking-config.js` (na pasta enviada ao site):

        window.AGUIA_CONFIG = {
          supabaseUrl: "https://SEU-PROJETO.supabase.co",
          supabaseKey: "SUA-CHAVE-ANON",
          table: "ranking"
        };

   A chave *anon* é feita para ficar no navegador. **Nunca** coloque a chave `service_role` aqui.

Como funciona: ao acabar a partida o jogador digita o nome e a pontuação é salva no aparelho **e** enviada ao
Supabase. O menu mostra duas abas: *Global* (top 10 do Supabase) e *Neste aparelho*. Se o serviço estiver fora
do ar ou sem internet, o jogo avisa e continua funcionando com o ranking local.

## Jogo

- **Controle:** arraste o dedo ou o mouse em qualquer ponto da tela (a águia acompanha o movimento, sem ficar
  coberta pelo dedo). Teclado: setas ou WASD. `P`/`Esc` pausam. A partida pausa sozinha ao trocar de aba/app
  ou ao deitar o celular (aparece o pedido para girar o aparelho).
- **Pontos:** joias +10 / +25 / +50; coelho +150 e +1 vida (máximo 5; começa com 4); cada nível dura 30 s e dá
  bônus de 200 × nível; zerar o nível 20 vale +2.000.
- **Perigos:** montanhas (sempre há passagem livre), tempestades com raios (nível 3+, anel amarelo avisa onde
  cai), gaviões (4+, em maior número nos níveis altos), chuva de meteoros (13+, linha vermelha avisa a trajetória).
- **Biomas:** campos (1–4), floresta (5–8), deserto (9–12), tundra (13–16), vulcão (17–20).
- **Salvamento:** automático a cada 4 s, ao pausar, ao mudar de nível e ao fechar. O menu mostra *Continuar* quando
  há progresso; *Novo jogo* pede confirmação antes de apagá-lo.

### Ajustar a dificuldade
Toda a curva está na função `cfg(l)` em `web/js/game.js` (velocidade, intervalo das montanhas, tempestades,
gaviões, meteoros) e nas constantes `LEVEL_TIME`, `MAX_HP`. Em simulação com um bot, os 20 níveis são
completáveis; como o jogo ainda não foi testado por pessoas, o ritmo ideal pode pedir ajuste fino.

## Testar no computador

    cd web
    python3 -m http.server 8000      # abra http://localhost:8000

(Abrir `index.html` direto do arquivo também joga, mas o navegador bloqueia o pré-carregamento das fontes e o
ranking global; para testar de verdade use o servidor acima.)

## Estrutura do projeto

    web/                  o site (enviar para a hospedagem)
      index.html, css/, js/ (storage, audio, ranking, game, app), assets/ (sprites e terrenos), fonts/
      ranking-config.js   credenciais do ranking global (vazio = só local)
    supabase.sql          tabela e regras do ranking global
    tools/build_web.py    gera dist/ (cópia do site) e dist-artifact/ (página única para publicar no Claude)
    tools/render_assets.py, optimize.py, postprocess.py   geram as artes (sprites e terrenos) a partir de código
    tests/                testes automatizados com Playwright (veja abaixo)
    pygame-referencia/    primeira versão em Pygame (desktop), mantida como referência

### Testes automatizados
Requer `pip install playwright` e `playwright install chromium`.

    python3 tools/build_web.py            # atualiza dist/
    python3 tests/t1_load.py              # carga e layout em desktop, iPhone e celular pequeno
    python3 tests/t2_flow.py              # menu, jogo, pausa, fim, continuar, toque e rotação
    python3 tests/t3_sim.py               # bot joga os 20 níveis; confere colisões e ausência de NaN/erros
    python3 tests/t4_visual.py            # capturas de tela por bioma
    python3 tests/t5_features.py          # níveis, autosave, vitória, ranking (Supabase e Claude simulados), offline
    python3 tests/t6_perf.py              # ritmo real de quadros no nível 20

## Limitações conhecidas

- **Fraude no ranking:** o cálculo da pontuação roda no navegador, então quem sabe mexer no cliente pode enviar
  números falsos. O limite por nível no SQL reduz o estrago, mas ranking à prova de fraude exige validação
  no servidor (por exemplo, uma Edge Function que repete a partida). Moderação de nomes é manual, pelo painel do Supabase.
- **Dispositivos reais:** os testes foram feitos em navegador automatizado (Chromium) com telas de desktop e
  de celular simuladas, toque simulado e sem GPU. Vale abrir no seu celular antes de divulgar.
- **Sem música**, apenas efeitos sonoros sintetizados (com botão de silenciar).
- O jogo reduz a resolução sozinho se o aparelho não consegue manter a fluidez.

## Licenças
Fontes Barlow e Barlow Condensed: SIL Open Font License (`web/fonts/OFL.txt`). Artes e código: do projeto.
