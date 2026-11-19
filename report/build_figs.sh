#!/bin/bash
# Renders the report hero figures (report/figs/*.png) from report/build_report_figs.js. Run before build_report.sh.
set -e
cd "$(dirname "$0")/.."
export NODE_PATH=${NODE_PATH:-$(pwd)/node_modules:$(npm root -g)}
node report/build_report_figs.js
cd report/figs && ${SOFFICE:-soffice} --headless --convert-to pdf report_figs.pptx arch_fig.pptx >/dev/null 2>&1 && pdftoppm -r 220 -png report_figs.pdf f && pdftoppm -r 300 -png -singlefile arch_fig.pdf architecture && pdftocairo -svg arch_fig.pdf architecture.svg
python3 - <<'PY'
from PIL import Image
a=Image.open('f-1.png'); w,h=a.size; a.crop((0,0,w,int(h*4.4/5.2))).save('cover_hero.png')
b=Image.open('f-2.png'); b.crop((0,0,w,int(h*5.0/5.2))).save('how_it_works.png')
PY
rm -f f-1.png f-2.png
