# Cross-deliverable QA record (2026-11-08, post-audit revision)

| Check | Result |
|---|---|
| Test suite | 77/77 pass (47 engine/e-HKD + 30 UI access-control / actor-identity) |
| Experiments | Full re-run; one canonical manifest (code `524a967dde0af4ba`); report and decks rebuilt from it |
| Clean-copy replay | Fresh copy of code + fixtures: 77/77; all results CSVs byte-identical except wall-clock timing columns (compute_time.csv, test_results.csv time_s, M-30) |
| Mutation analysis | 13/14, harness guarded against spurious kills (unmutated sandbox must pass) |
| UI access | Flask over HTTP for 9 principals (ledger, export, operator controls); Streamlit via stub for 9 principals: no account leaks |
| Actor identity | Journal actor equals selected participant for every offered action and every autoplay step |
| Screenshots | 24 re-captured from the fixed Flask build by browser clicks (capture_log.json shows "as <principal>" in every flash) |
| Report | Counted body pages 4–15 = 12 pages (limit 15); 21 pages total; 19 DOCX hyperlinks, PDF URI annotations present |
| Decks | Interim 14 slides (7 main), Final 22 slides (12 main); validate.py PASSED; no ZIP folder entries; theme colours applied |
| Statistic consistency | Automated scan of report/deck PDFs and speaker scripts: no stale "47/47"; 77/77, 17/17, 13/14, 57.1 / 28.6 consistent |
| Risky phrasing | "tamper-proof" only in negation; no "regulatory approval", "HKMA-approved" |
| Proposal | Not modified |

**Open items for the team:** recorded Streamlit walk-through; peer feedback (report §7.4); four reflections (App. A);
confirm AI acknowledgement (App. F); sign academic-honesty declaration; confirm presentation slot; assign speakers;
`npm install` once on a student laptop to confirm the clean rebuild and create a lockfile.
