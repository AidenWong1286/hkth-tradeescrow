# CLAUDE.md — working guide for HK–TH TradeEscrow (FTEC3002 Group 1)

Python escrow prototype (synthetic data only) + the generators for the final report (.docx/.pdf) and final deck (.pptx).
Everything a reader sees is **regenerated from `results/`**, so after any code change you rebuild instead of hand-editing numbers.

## Commands
```bash
pip install -r requirements.txt          # Python >= 3.11; engine is stdlib-only
npm install                              # Node >= 20 (pptxgenjs, docx, react-icons + sharp for icons)
python -m pytest -q                      # 91 tests must pass
streamlit run ui_streamlit/streamlit_app.py      # proposal UI
python -m ui_flask.app                   # Flask console -> http://127.0.0.1:5050
bash scripts/rebuild_all.sh              # tests -> results -> diagrams -> charts -> report -> deck (needs LibreOffice + poppler-utils)
SKIP_DECK=1 bash scripts/rebuild_all.sh  # report only
```
The report build prints two numbers: Sections 1–10 (incl. self-reflections) with figures, and `Text-only body (figures excluded) = N pages` (a figure-free rebuild, `NOFIG=1`).
The course outline §10 excludes figures, so **the text-only number must stay ≤ 15** (currently 10).

## Layout (only what matters)
| Path | What it is |
|---|---|
| `tradeescrow/model.py` | states, roles, PERMISSIONS, TRANSITIONS (source of truth for the state machine) |
| `tradeescrow/escrow.py` | EscrowService: commands, 7-check release guard, token accounting, hash-chained journal |
| `tradeescrow/offchain.py` · `views.py` · `ehkd.py` | simulated document/KYC modules · role projections · e-HKD 2-phase illustration |
| `tradeescrow/process_model.py` | BPMN tasks/flows for baseline vs escrow (drives Figures 3–4, 6–8) |
| `tradeescrow/ui_actions.py` | shared action layer used by BOTH UIs |
| `ui_streamlit/`, `ui_flask/` | the two front-ends (Flask is the verified fallback demo) |
| `tests/` | 91 tests incl. UI access control (`test_ui_access.py`) |
| `scripts/run_experiments.py` | writes every CSV in `results/` + `metrics.csv` (M-01…M-34) |
| `scripts/make_slide_diagrams.py` | hand-laid architecture, state machine, two-tier BPMN (deck versions) |
| `scripts/make_report_diagrams_v4.py` | same diagrams re-coloured for the report → `diagrams/report/` |
| `scripts/make_report_charts_v3.py` | Figures 6–8 → `results/charts/v3/` |
| `report/build_report.js` | **all report text**, tables, figure placement (docx-js) |
| `report/make_report_graphics.py` | part openers, running heads, 7 "In brief" graphics, callout side graphics |
| Self-reflections | Section 10 of the body (`REFLECTIONS` in `report/build_report.js`); counted in the 15 pages |
| `report/make_glance.py` · `make_covers_AD.py` | page 2 "at a glance" · covers (D is used; `COVER=report/figs/cover_A.png` to switch) |
| `presentation/build_final_paper.js` + `part3_upgraded.js` | final deck (slides 9–12 = Part 3) |
| `official_inputs/` | course outline (rubric, page limit) and the submitted proposal |
| `docs/` | domain model, evaluation method, limitations, peer-feedback protocol |

## If you change the UI or a function — what to update
**Automatic (just run `bash scripts/rebuild_all.sh`):** every metric and count in the report, page 2, part openers, Table 4, the
7 "In brief" graphics that read CSVs (tests, attacks, robustness, mutants, roles grid, TC-001 journal), Figures 3–4 and 6–8, deck charts.

**Manual — check these by hand after the change:**
| You changed… | Update |
|---|---|
| **UI look / pages** (Streamlit or Flask) | 1) start Flask, run `python scripts/capture_screenshots.py` (Playwright) → `results/screenshots/`; 2) fix crop boxes in `scripts/make_slide_assets.py` (`CROPS`) → `presentation/assets/S_TC00x_panel.jpg` (report Figure 5, deck slide 9); 3) report text: §4 first paragraph ("Streamlit app, Flask console…"), §6.1 bullets "UI end-to-end check" and "UI access-control regression tests", §8 "Evidence base", Appendix G changes list; 4) deck slide 11 "after" panel is transcribed from the real page — re-check it. |
| **A state / transition** (`model.py TRANSITIONS`) | edges are hand-placed in `scripts/make_slide_diagrams.py::state_machine()` (Figure 2 + deck); Figure 2 headline in `HEADS` ("Fifteen permitted transitions…"); part-2 opener numbers in `make_report_graphics.py OPEN[2]`; §5 text. |
| **Release-guard checks** (`escrow.py`) | `make_report_graphics.py` → `gates` list (g_guard); §5.1 text; HEADS/ES1 wording; guard label in `state_machine()`. |
| **Roles / permissions / visibility** | `make_report_graphics.py` → `ROLE` and `CAP` lists (g_roles); Table 3 rows in `build_report.js`; architecture boxes in `make_slide_diagrams.py::architecture()`. |
| **Scenario paths TC-001/002/003** | `make_report_graphics.py` → `strips` (g_paths: states + reason codes are typed there). |
| **Process steps / durations** | `tradeescrow/process_model.py`, `results/baseline_assumptions.csv`; HEADS for Figures 3, 4, 6 and the Part-3 standfirst ("about half the size…") if 7→3 / 7→5 changes. |
| **Number of tests / attacks / mutants** | automatic, except the hard-coded headline `HEADS["Table 4"]` ("13 of 14") and `HEADS["Figure 6"]` ("7 → 5 … 7 → 3"). |

Hard-coded wording to re-read after any change: `HEADS` and `H2CHIP` in `report/build_report.js`; `OPEN` standfirsts in `report/make_report_graphics.py`.

## Peer feedback (§7.4)
Enter REAL anonymised responses in `results/survey_anonymised.csv` (columns as in `results/survey_anonymised_TEMPLATE.csv`, Q1–Q5 = 1–5),
then rebuild: the §7.4 paragraph and the diverging-bar chart are generated from that file. Never simulate responses.

## Rules
- Synthetic data only; never invent survey results, peer feedback, timings or screenshots. Pending items stay labelled pending (red `TEAM TO COMPLETE` text in the report).
- Keep the palette: navy `#0B1730`, teal `#1F8A82` (tested/passed), gold `#B07A22` (modelled/key), red `#B8342A` only for refusals/exceptions.
- Text-only body ≤ 15 pages (build line); avoid half-empty pages.
- Log each change in `CHANGELOG.md`.
- Background spec from early in the project: `docs/background/guidance.md` (may be outdated — code and `results/` win).
