#!/usr/bin/env bash
# One command that regenerates every number, figure, the report and the final deck, in dependency order.
# Usage: bash scripts/rebuild_all.sh            (from the project root)
#        SKIP_DECK=1 bash scripts/rebuild_all.sh   (report only)
set -euo pipefail
cd "$(dirname "$0")/.."
export NODE_PATH="${NODE_PATH:-$(npm root 2>/dev/null)}:$(npm root -g 2>/dev/null)"
step() { printf '\n== %s\n' "$*"; }

step "1/7 tests";                    python -m pytest -q
step "2/7 experiments -> results/";  python scripts/run_experiments.py && python scripts/update_registers.py
step "3/7 BPMN XML + diagrams";      python -c "import sys; sys.path.insert(0,'scripts'); import make_diagrams as d; [d.write_bpmn(m) for m in ('baseline','proposed')]"
                                      python scripts/make_slide_diagrams.py
                                      python scripts/make_report_diagrams_v4.py
step "4/7 charts + report graphics"; python scripts/make_report_charts_v3.py
                                      python report/make_report_graphics.py
                                      python report/make_glance.py
                                      python report/make_covers_AD.py
                                      bash report/build_figs.sh
step "5/7 UI screenshot crops (only if results/screenshots exists)"
if [ -d results/screenshots ]; then python scripts/make_slide_assets.py; else echo "skipped: run scripts/capture_screenshots.py with the Flask app up to refresh screenshots"; fi
step "6/7 report";                   bash report/build_report.sh
if [ -z "${SKIP_DECK:-}" ]; then
step "7/7 final deck";               node presentation/build_final_paper.js && python scripts/export_speaker_notes.py
fi
echo; echo "Done. Check: counted body <= 15 pages (line above), then open report/*.pdf and presentation/*.pptx."
