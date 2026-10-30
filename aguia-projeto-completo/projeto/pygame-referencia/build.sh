#!/usr/bin/env bash
# Gera a pasta dist/ pronta para hospedar (site estático). Requer: pip install pygbag
set -e
cd "$(dirname "$0")"
rm -rf .stage dist && mkdir -p .stage/aguia
cp main.py game.py storage.py .stage/aguia/ && cp -r assets .stage/aguia/
python3 -m pygbag --build .stage/aguia
cp -r .stage/aguia/build/web dist
python3 tools/postprocess.py dist
echo "Pronto: envie TODO o conteúdo da pasta dist/ para a hospedagem."
