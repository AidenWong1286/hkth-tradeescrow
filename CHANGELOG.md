# Change log

## 2026-11-20 — Report v4: modern restyle, content upgrades, screenshot appendix, git
- **Report `_v4.docx`** (OneDrive), built from `_v3`: headings Georgia → Segoe UI (Semibold for bold) with exact 1.2× line height so pagination holds; all 30 design graphics regenerated and swapped at identical pixel sizes (page frames with brand mark + teal journal chain + run hash, part openers with the guard ring as progress, "At a glance", every "In brief" graphic — the five "77" images now read 91). Sections 1–10 still span 15 pages (now pp. 5–19; the old near-empty page 5 is gone). Validated with the docx skill (all edits tracked).
- **Tracked content edits:** §9 "Launch path and secondary services" (4 phases + escrow-enabled services); Table 4 compute time 3.71 → 4.06 ms (run of record); Appendix E source-code and demo-video links as red TEAM TO COMPLETE placeholders + pointer to Appendix I; Appendix G note on the console fix below.
- **Appendix I (new, portrait section):** 21 captioned screenshots from `scripts/capture_walkthrough.py` (all states reached through the console's own controls).
- **Console fix:** a participant outside the trade (importer #2) could still see the escrow's state word; `ui_flask/app.py` now hides it, with a regression assertion in `tests/test_ui_access.py` (91 tests pass). Top-bar tabs no longer wrap.
- **Graphics scripts ported to Windows:** `report/make_report_graphics.py` and `report/make_glance.py` use Segoe UI/Consolas and render SVG with Edge (Playwright) instead of `rsvg-convert` and Linux fonts.
- **Public-repo privacy:** student IDs moved out of tracked files into `team.local.json` (git-ignored; template `team.example.json`). `report/make_cover_v3.py`, `report/make_covers_AD.py`, `report/build_report.js`, `presentation/build_final_paper.js` and `presentation/build_deck_v4.py` read it and fall back to names only; footers in `presentation/v4/source_content.json` no longer carry IDs. Verified: local builds still print the IDs; no staged file contains one.
- **Git / GitHub:** published at https://github.com/AidenWong1286/hkth-tradeescrow (public). Repo-local identity uses the account's GitHub noreply address. Report `_v4` Appendix E now carries this link (tracked insertion); the demo-video link is still TEAM TO COMPLETE. `.gitignore` now excludes `official_inputs/`, cover images and local tooling; README updated (91 tests, console, screenshot scripts, current robustness numbers). Student IDs remain in five generator sources (team decides public vs private).

## 2026-11-19 (late) — Colour deck v5 and new report cover (report content unchanged)
- **Deck v5 (colour)**: `presentation/build_deck_v4.py` now builds the v4 layout in the project palette with fixed meanings (navy structure, teal tested/passed, gold money/modelled, red refused/risk) → `presentation/HKTH_TradeEscrow_Final_Presentation_v5_colour.pptx` (+ OneDrive). Photos are navy→teal duotones (`presentation/v4/make_duotone.py` → `photos_duo/`), the mesh is teal (`render_mesh.py` variant `mesh_teal`), ring/footer chain/nav in teal, HKD flows and modelled results in gold. The monochrome v4 file is kept as it was.
- **Report cover v3**: `report/make_cover_v3.py` (HTML rendered by Edge, Segoe UI) → `report/figs/cover_v3.png` (2480×3508, same size as before). Same information as the old cover; numbers from `results/` (91 tests, 17 attacks, 0/5,935, −28.6% modelled, run hash `b5f2334b`). Swapped into a copy of the `_v2` report → `_v3.docx` in OneDrive; all other pages, text and tracked changes are untouched.

## 2026-11-19 (night) — Final deck v4 "Corridor": off-white monochrome, tailored to the product
- **New generator** `presentation/build_deck_v4.py` (python-pptx; Node is not installed on this machine) → `presentation/HKTH_TradeEscrow_Final_Presentation_v4.pptx` (also copied to OneDrive). Same 26 slides, order, presenters and speaker notes (`presentation/v4/source_content.json`, extracted from the `_v2` deck).
- **Design system:** paper `#F5F5F2`, card `#EBEBE7`, ink `#111111`, secondary `#6E6E73`, hairline `#D6D6D0`; teal/red only as pass/refusal signals. Segoe UI Semibold/Light/Regular + Consolas (standard Windows fonts).
- **Product motifs:** 7-segment release-guard ring (slides 7, 8, 15), hash-chain footer as slide progress, the console's wave mesh rendered by `presentation/v4/render_mesh.py` from `ui_flask/static/mesh.js`, HK → Laem Chabang route line on the cover, light-theme console screenshots (slides 9, 11, B6), state machine redrawn natively with the console's lifecycle geometry (B2).
- **Photos:** 6 Unsplash photos (Unsplash License), toned monochrome by `fetch_photos.py` → `presentation/v4/photos/` (+ CREDITS.txt); credited on the Sources slide.
- **Numbers from results/:** every figure is read from `metrics.csv`, `process_counts.csv`, `timelines.csv`; stale "6,000 random checks" on old slides 5, 8 and 12 now reads 5,935 (M-09).
- Everything except photos, mesh and screenshots is a native editable shape; theme hyperlink colour set to ink. Verified by rendering all 26 slides (LibreOffice) and fixing overlaps.

## 2026-11-19 (evening) — Report and deck updated for the redesigned console (copies saved as `_v2`)
- **Re-run of record** `scripts/run_experiments.py` (run with `PYTHONUTF8=1` on Windows, otherwise the CSVs are written in the system code page): only M-01 changed, 77/77 → 91/91 (M-30 wall-clock varies by machine). Mutation still 13/14. Code hash `b5f2334b6c31ab71`. Previous `results/` kept in the session scratchpad.
- **Screenshots:** new `scripts/capture_screenshots_v2.py` (Playwright + the installed Microsoft Edge, states reached via `/sim/step`) → `results/screenshots/v2/` (dark + light: TC-001 released, TC-002 refused/Under Review, TC-003 refused/Frozen, regulator ledger, laptop-shaped TC-001, Figure 5 stage crop). `presentation/assets/S_TC003_panel_v2.jpg` = new Figure 5.
- **Report `_v2.docx`** (tracked changes, author "Claude (AI-assisted edit)"): 77 → 91 in exec summary, §4, §9, Appendix B line, Table 4, exec tile and Appendix A; §6.1 browser wording; Figure 5 image + source line; §8 evidence base; §6.3 and Appendix E run of record; new Appendix G item. A Word comment on Appendix F asks the team to update the AI declaration (the redesign used Claude Code). Length unchanged (Sections 1–10 still end on page 20 in a LibreOffice render).
- **Deck `_v2.pptx`:** slide 2 and 10 test counts; slide 9 laptop screenshot (now fills the screen opening) + "what to watch" line + notes; slide 10 robustness numbers corrected to results (0 / 5,935 checks; 5,312 commands, which had been stale); slide 11 AFTER panel; slide 23 B6 screenshots, cards and captions. Slide 11's 47 → 77 history left unchanged.
- **Generator synced:** `report/build_report.js` wording/figure path; `report/make_covers_AD.py` reads the test count from `results/metrics.csv` instead of a hard-coded "77".
- **Still showing 77 (images):** cover, page 2 "at a glance", g_testdesign, g_metrics, g_appB. Regenerating them needs `rsvg-convert` and the Inter / Gelasio / Crimson Text / DejaVu Sans Mono fonts, which this Windows machine does not have.

## 2026-11-19 (later) — Console restyled "Ink & Signal": monochrome, wave-mesh background, light/dark (no engine change)
- **Palette:** black/white interface (`#0A0A0A` dark, `#F4F4F2` light); colour only as a status signal — teal `#1F8A82` = passed/released, red `#B8342A` = refused/frozen/under review. Gold removed from the UI (report and deck palettes unchanged).
- **Background:** `ui_flask/static/mesh.js` — animated 2D SVG wireframe wave mesh (two diagonal ribbons, 34 × 1px hairlines + faint cross-lines each, `rgba(255,255,255,.15)`), ~30 fps, paused when hidden, static under reduced motion. Masked down behind the content area and dimmed while data animations run; panels have a near-solid backing so text never sits on moving lines.
- **Theme switch** in the top bar (dark by default, choice remembered in `localStorage`, no flash on load).
- **Console:** large thin state word that slides on each transition (with a teal/red signal dot), thin-line 7-check ring, white orb with a light trail for HKD movements, hairline lifecycle map, monochrome rail/guard/chain/audit.
- **Cinema mode** (film bar button or `C`): hides the side rail and enlarges captions for recording.
- **New `/intro` page** for the video opening; its figures (7 checks, 8 roles, 15 transitions, 3 scenarios) are read from the code.
- Ledger and e-HKD pages restyled to match. 91 tests still pass. Report Figure 5 / deck screenshots still to be recaptured.

## 2026-11-19 — Flask console redesign: animated "trade corridor" (no change to engine rules, data or metrics)
- **Look:** dark navy theme in the report palette (teal = passed, gold = HKD/key, red only for refusals/exceptions); Bahnschrift / Segoe UI / Cascadia Mono system fonts (works offline). New `ui_flask/static/console.css`; all four templates rewritten.
- **Console layout:** participant rail (one click per role) · trade corridor (HK importer vault → escrow ring → Thai exporter vault) · lifecycle "metro map" with the travelled path · release-guard checklist · full-width hash-chain ribbon · role lens with hatched hidden fields · audit trail.
- **Animation layer** `ui_flask/static/console.js` (progressive enhancement; every page still works as plain forms): intercepts posts, swaps the re-rendered page and animates the diff — 7-check guard sequence (shake on a refused release), HKD token flight with counting balances, comet along the lifecycle edge, sliding audit rows, chain-crack cascade, role-lens scan. Animations replay journalled results only; the `#snap` JSON is built from data the role can already see. `prefers-reduced-motion` respected.
- **Film mode** (operator, loopback only): bottom player replays TC-001/002/003 one step at a time via new `/sim/step`, each step as its real principal (`ui_actions.run_autoplay_step`, same steps/clock as `run_autoplay`). Space bar plays/pauses.
- **Tamper demo** (operator, loopback only): `/sim/tamper` edits one stored event without re-hashing so `verify_journal()` fails; reset restores.
- **Live guard colouring:** in Bank H's live view an unmet check is shown as "waiting" (neutral), not red; red is used only for refused attempts and holds/freeze/review.
- **Tests:** +14 in `tests/test_ui_access.py` (77 → 91): film steps = autoplay (actors, operations, outcomes, path) for all three scenarios; new controls gated (disabled / non-loopback / unknown variant); tamper breaks and reset restores the chain; console snapshot and vault amounts obey each role's projection for all 9 participants.
- **Not yet done (manual, per CLAUDE.md):** rebuild (`bash scripts/rebuild_all.sh`) so M-01 shows 91 tests; recapture screenshots and crops for report Figure 5 / deck slides 9 and 11; update report §4, §6.1, §8 and Appendix G wording for the new UI.

## 2026-11-19 — Robustness harness fix (found in final review)
- **Defect:** after the 8 Nov change `run_action(svc, action, variant, actor_id)`, `scripts/run_experiments.py` still called `run_action(s, a, variant)`. Every call raised `TypeError`, which the bare `except` counted as a refusal — so the study ran 0 accepted / 5,427 refused commands and never created an escrow; "0 violations / 6,000" was vacuous.
- **Fix:** canonical steps now replay `autoplay_steps(variant)` with their real principals; random steps use the action's owner (50%) or a random participant (exercises RBAC refusals). Harness errors (`TypeError`/`AttributeError`/`NameError`) are counted separately and stop the run.
- **New result (seed 3002):** 200 trades, 5,312 commands — 2,206 accepted, 3,106 refused; final states Released 57, Frozen 64, Refunded 30, Pending 26, Under Review 8, No escrow 15; **0 violations in 5,935 invariant checks**. M-09/M-10 updated; all other metrics unchanged (M-30 is wall-clock and varies).
- Final deck Part 3 (slides 9–12) upgraded; slide 11 reports this as the third "green result that was wrong".

## 2026-11-18 — Visual redesign v3 (no change to engine, data or numbers)
- **Final deck v3** `presentation/build_final_v3.js` → `HKTH_TradeEscrow_Final_Presentation_v3.pptx`: dark theme (`presentation/v3/`: backgrounds, Lucide icons via react-icons + sharp, `style3.js`), 16 main + 10 backup slides, native dumbbell / Gantt / doughnut charts, new state-machine slide, demo slide. PowerPoint **Morph** transitions on every slide (Fade fallback); objects named `!!…` are paired across slides. Font: Inter. Speaker notes carried over from v1.
- **Report figures**: Figure 1 redrawn (`report/build_report_figs.js` → `report/figs/architecture.png`), Figure 2 regenerated (`scripts/make_state_machine_v3.py`), Figures 6–8 redesigned (`scripts/make_report_charts_v3.py`, SVG + PNG), new Appendix H with landscape full-size diagrams; cover, Figure ES1 and results strip (`report/build_figs.sh`).
- Build order: `python scripts/make_state_machine_v3.py && python scripts/make_report_charts_v3.py && bash report/build_figs.sh && bash report/build_report.sh && node presentation/build_final_v3.js`.

## 2026-11-08 — Revision after the Independent Audit & Revision Plan

Run of record after this revision: `results/run_manifest.json` (code hash `524a967dde0af4ba`; previous `edb2545eeafa4f45`).
Verified functionality, evidence and valid results were preserved; nothing was rebuilt from scratch.

### P0 — critical technical fixes
| Item | Change | Files |
|---|---|---|
| P0-1 UI data-access bypass (user issue 1) | New server-side projection `views.ledger_view`: Bank H ops/compliance full ledger; importer/exporter own accounts and own-trade events; regulator and Bank O metadata only; logistics/customs denied and logged (READ REJECTED). Flask `/ledger` returns 403 when denied; the Streamlit Ledger tab uses the same projection. Locked amount and total supply are no longer shown to roles without amount visibility. | tradeescrow/views.py; ui_flask/app.py; ui_flask/templates/{ledger,index,base}.html; ui_streamlit/streamlit_app.py |
| UI actor identity (user issue 2) | `run_action(svc, action, variant, actor_id)` runs every button as the participant selected in the UI. Importer #2 pressing *Create & fund escrow* is now refused (NOT_TRADE_BUYER) and journalled as `u_importer_02`; Bank H ops runs document matching and release; compliance runs screening. Autoplay passes explicit principals (`run_autoplay`). Flash messages show the acting principal. | tradeescrow/ui_actions.py; both UIs |
| Demo scope controls | `/sim/*` operator controls served to loopback clients only, can be disabled (`TRADEESCROW_DEMO_CONTROLS=0`), unknown controls → 404; service identities cannot be selected in the UI; per-process random session key; UI and docs state that "Act as" is impersonation, not authentication. | ui_flask/app.py; templates; README |
| Regression tests | +30 tests (47 → 77): HTTP tests for every participant on `/ledger` and `/export.json`, operator-control gating, off-menu actions, service-identity selection, and journal actor = selected participant for every offered action and every autoplay step. | tests/test_ui_access.py |
| Streamlit | Stub smoke test now renders every participant and checks the Ledger tab shows no other party's accounts; team-reported local launch recorded; full click-through still open. | scripts/dev/streamlit_stub*/ |
| Mutation harness defect found during re-run | The sandbox did not copy `ui_flask`, so the new test module failed to import and every mutant looked "killed" (14/14). The harness now copies `ui_flask`, refuses to score if the unmutated sandbox fails, and treats collection errors as errors, not kills. Result unchanged at 13/14. | scripts/run_experiments.py |
| Screenshot capture race | Role switching now waits for the form-submit navigation, so each capture reflects the selected role. Ledger screenshot is now taken as Bank H (it had been taken as importer #2 under the bypass). New captures: importer #2 rejected, ledger as importer #2 / regulator / logistics. 24 screenshots re-captured. | scripts/capture_screenshots.py; results/screenshots/ |

### P1 — evidence framing, references, portability
- **Efficiency comparison (P1-4).** All process charts/captions labelled "team-defined process model; not measured industry savings" or "assumption-driven, simulated days". Added a matched-scope sensitivity variant `proposed_e2e` (hypothetical redemption, cross-bank payment, Bank O credit, reconciliation, using the baseline's own durations): manual tasks 7 → 5 (28.6%), latency 7.0 → 2.25 days, importer cash committed 9.25 days (metrics M-31…M-34). Report: boundary table (Table 3a), matched-scope paragraph, central-database benchmark and demo-security limitations; 48 h window and HKD 5m limit labelled team parameters (also in run_manifest `rule_config`).
- **References (P1-5).** Report URLs are now clickable hyperlinks (DOCX `w:hyperlink`, PDF URI annotations); final deck sources clickable (B8, F2, F12). Ref [6] now points to the exact EXIM Thailand release (re-verified 8 Nov 2026); CargoX figure marked as an estimate from KPMG desktop research; e-HKD Phase 2 marked as mainly retail use cases.
- **Portability (P1-6).** `package.json` with pinned pptxgenjs 4.0.1 / docx 9.8.1 and tested versions; project-local `presentation/apply_theme.js` replaces the external skill script (also strips ZIP folder entries); `report/build_report.sh` uses plain `soffice` (override with `SOFFICE`); Node/npm/Python/LibreOffice versions recorded.

### Slides
- **Interim** redesigned to 13.33 × 7.5 in: 7 main slides (status, trade-off strip, 5-block architecture, three gates, TC-001, TC-002/003, evidence + open items with dates) + appendix (full state machine, architecture, both BPMNs one per slide, scenario table, ledger fix). Titles 30 pt, body 17–24 pt. The 92.5% headline replaced by functional status; tracker shown as a small label (now 93.75%, workstream J 0.5 → 0.75).
- **Final** redesigned: 12 main slides following audit F1–F12 + 9 backups (full diagrams, permissions, ledger fix, e-HKD cases, clickable sources, demo fallback/Q&A). Native editable charts for the process inventory (incl. matched scope) and the financing trade-off; evidence-type tags on every evidence slide; speaker notes state what each visual does and does not prove.
- New cropped assets from the real screenshots via `scripts/make_slide_assets.py` (crop only; no drawing on pixels). Speaker scripts regenerated from deck notes (`scripts/export_speaker_notes.py`).

### Unchanged
Engine rules, fixture, 63/63 assertions, 17/17 blocked releases, 0/6,000 invariant violations, 32/32 audit events, 5/5 e-HKD cases, 7 → 3 and 7.0 → 0.5 model results. The submitted proposal was not modified.

## 2026-11-19 — Report visual redesign (cover palette)
- New full-page cover (report/make_covers_AD.py, cover D; set COVER=report/figs/cover_A.png to switch) and "Report at a glance" page (report/make_glance.py).
- Report styles, call-outs, KPI strip and all figures (charts, state machine, BPMN, hero figures) recoloured to navy #0B1730 / teal #1F8A82 / gold #B07A22; red only for exceptions. BPMN PNGs re-rendered at 300 dpi.
- No wording or numbers changed. Body still 13 pages (PDF pages 6–18); 28 pages total.

## 2026-11-19 — Report interior redesign (v4 design system)
- Running head band, part openers (4), finding-first exhibit headlines (original captions kept as source lines), evidence chips, restyled tables with status tags, key-finding boxes with side graphics.
- Seven new data-driven "in brief" graphics (report/make_report_graphics.py): weaknesses strip (§1.2), H1–H5 evidence ladder (§3), seven-check release guard (§5.1), role-visibility grid (§5.3), four test layers (§6.1), flagship state paths (§7.1), TC-001 journal (§7.3).
- Table 4 gains a Status column. Body text 10.5 pt. Counted body = 15 pages including all figures (PDF pages 6–20); 30 pages total.

## 2026-11-19 — Report figures v4
- Figures 1–4 replaced by the team's readable layouts (two-tier BPMN joined at connector A, flow architecture, hand-laid state machine), re-coloured to the report palette at 300 dpi by scripts/make_report_diagrams_v4.py (diagrams/report/). Appendix H uses the same images full-size.
- Figure 2 caption corrected (teal/red colours; transitions match tradeescrow/model.py). Process maps placed before Table 3a. Counted body still 15 pages (PDF 6–20).

## 2026-11-19 — Report v5 page design
- Full-page frame behind every page (white running head with HK/TH monogram, journal strip, ledger spine in the margin, footer rule); page number in the footer.
- Front matter flows into Part 1 (no forced page break); contents fit one page; Figure 1 back to the card architecture.
- New data graphics: sensitivity ranges (§7.2, Table 5 moved to Appendix D), peer-questionnaire chart driven only by results/survey_anonymised.csv, Appendix B test/robustness dashboard, Appendix C attack refusals.
- Build measures the course-defined count (figures excluded) via a NOFIG rebuild: 10 pages. Wong Ho Ming's reflection added (AI-assisted, labelled).

## 2026-11-19 — Report v6: fewer gaps, four more graphics
- New graphics: initiative layer stack (§2), open account / escrow / L/C comparison (§2.1), six metric families (§6.3), five-step roadmap (§9).
- Key-finding boxes may split across pages; references and appendices flow on without forced page breaks; charts slightly smaller. Text-only body 9 pages.

## 2026-11-19 — Report v7: reflections in the body, data-analysis graphics
- Self-reflections moved into the counted body as Section 10; Appendix A is now a map of assessment elements. Text-only body 10/15 pages.
- New graphics: manual work by participant (§7.2), TC-001 journal timeline by actor (§7.3), audit scorecard per scenario (§7.3), planted bug → catching test (§7.1).

## 2026-11-19 — Report v8: Sections 1–10 fit in 15 physical pages, figures included
- Body figures scaled (FIGSCALE 0.65; Appendix H full size), 10 pt text, wider text block, tighter spacing; no forced page break after contents (fixes a blank page in Word).
- Detail tables moved to appendices (Table 2 and 3a → App. D, Table 3 → App. C, metric tiles → App. A); their summary graphics stay in the body.
- Sections 1–10 = PDF pages 5–19 (15 pages including every figure); Section 10 starts on p.18 with room for teammates' reflections.

## 2026-11-19 — Report v9: page numbers on counted pages only
- Sections: front matter (no numbers) · Sections 1–10 numbered 1–15 · references and appendices (no numbers). Contents shows body page numbers, and "PDF n" for unnumbered parts.
- Executive summary fits one page; last counted page keeps space for teammates' reflections.
