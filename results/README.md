# results/ — evidence bundle (regenerate: `python scripts/run_experiments.py`)

| File | Contents |
|---|---|
| run_manifest.json | Run time, code hash, fixture version, Python, seed, rule config |
| test_results.csv, pytest_report.xml, pytest_output.txt | pytest results |
| scenarios_summary.csv, assertions.csv, events/*.jsonl | Flagship scenario runs (TC-001, TC-002/R/T, TC-003/C/T) with full hash-chained event logs |
| control_matrix.csv | 17 unsafe release attempts + 1 positive control |
| audit_completeness.csv, audit_access_matrix.csv | Auditability and role-visibility checks |
| robustness.csv | 200 randomised trades (seed 3002) |
| mutation_analysis.csv, mutation_analysis_run1_before_test_fixes.csv | Seeded-defect detection, runs 2 and 1 |
| process_counts.csv, timelines.csv, baseline_assumptions.csv, measured_human_commands.csv | Comparator (MODEL / ASSUMPTION-DRIVEN) |
| ehkd_results.csv | e-HKD two-leg cases |
| compute_time.csv | Wall-clock engine timing (environment-dependent; NOT settlement time) |
| metrics.csv | Headline metrics with denominator, unit and claim type |
| charts/*.png | Charts generated from the CSVs above |
| screenshots/*.png | Real UI captures from scripts/capture_screenshots.py (Flask, 7 Nov 2026) |
| survey_anonymised_TEMPLATE.csv | Peer-feedback template (no data yet) |
