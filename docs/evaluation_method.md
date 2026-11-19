# Evaluation method

All numbers in the report and slides come from `results/` produced by `python scripts/run_experiments.py`
(manifest: `results/run_manifest.json`). Three kinds of quantity are kept separate:

| Kind | Examples | Status |
|---|---|---|
| **SIMULATION_RESULT** | test pass counts, blocked unsafe releases, audit completeness, RBAC rules obeyed, robustness, mutation detection | Produced by running the prototype |
| **MODEL (BPMN inventory)** | manual task counts | Counted from the two process models in `tradeescrow/process_model.py` (same source as the BPMN files) |
| **ASSUMPTION-DRIVEN MODEL** | durations, latency, lock-up, HKD-days | Computed from team-stated low/base/high durations (`results/baseline_assumptions.csv`), fixed **before** comparison; not empirical |

## Comparator design
* Same trade (HKD 250,000), parties, documents, shipment milestone and two compliance checkpoints in both models.
* **Baseline** = open account: exporter ships first, documents are sent to the importer, the importer checks them, waits for the
  payment term (0 or 30 days), instructs payment; Bank H screens and approves; Bank O credits; exporter reconciles.
* **Proposed** = pre-funded escrow: importer funds before shipment; creation screening; lock; shipment and documents attested;
  automated matching; pre-release screening; guarded release.
* Goods preparation, customs clearance and carriage are **common** tasks (same durations in both) and excluded from settlement-task counts.
* Exception classes: `mismatch` adds one manual review task to each model; `aml` adds one compliance investigation task to each.
* Automated engine steps are modelled as 0 business days. This is an optimistic assumption: real oracle, screening and bank
  processing latency is not zero.

## Matched-scope sensitivity variant (added 8 Nov 2026 after the independent audit)
The baseline ends when Bank O credits the exporter and the exporter reconciles; the prototype ends when Bank H
releases a synthetic HKD claim that Bank O only acknowledges. This asymmetry flatters the escrow. `proposed_e2e`
in `process_model.py` replaces the Bank O observation with the hypothetical steps needed to reach the same end
point (exporter redemption instruction, Bank H payment message = B10, Bank O credit = B11, reconciliation = B12),
re-using the baseline's own durations. It is **not implemented** in the prototype and is reported as a sensitivity
check (metrics M-31…M-34): manual tasks 7 → 5 (28.6%) instead of 7 → 3 (57.1%). FX is excluded in all models.
All process figures are a **team-defined process model, not measured industry savings**. A central shared database
could implement the same rules; these results say nothing about the advantage of DLT consensus.

## Metric definitions
| Metric | Definition |
|---|---|
| Process steps | Executed tasks in the model for the scenario class (gateways reported separately) |
| Manual effort | Count of `MANUAL` settlement tasks (person performs or approves). Cross-checked against **human-role commands executed in the prototype** (`measured_human_commands.csv`) |
| Execution accuracy | Correct assertions ÷ total assertions across 7 flagship runs (`assertions.csv`) |
| Release/exception safety | Unsafe release attempts blocked with funds unchanged ÷ total unsafe attempts (`control_matrix.csv`), plus a positive control that must release |
| Transparency / role visibility | Visibility rules obeyed ÷ rules specified, 9 principals × 7 capabilities (`audit_access_matrix.csv`) |
| Auditability | Required lifecycle events present with all mandatory fields ÷ required (`audit_completeness.csv`), whether the regulator can reconstruct the state path from metadata only, commercial leakage probes, hash-chain verification |
| Compliance coverage | Both KYC/AML checkpoints enforced (TC-005, TC-010, TC-011, NC-06..NC-11) |
| Post-shipment latency | t(credit) − t(shipment) |
| Full cycle | t(credit) from contract signature |
| Importer funds committed | t(credit) − t(importer funds leave), in days and HKD-days |
| Exporter unsecured receivable | days between shipment and credit **without** payment security (0 in escrow because funds are locked before shipment) |
| Robustness | 200 synthetic trades, seed 3002, 30 random steps each (60% next canonical step, 40% any action incl. forbidden); invariants checked after every step |
| Test-suite strength | Mutation analysis: 14 seeded defects in the guard, RBAC, journal, views and matching; killed = suite fails |
| Engine compute time | Wall-clock ms (median of 30) — environment-dependent and **not** a settlement time |

Formulae: reduction % = 100 × (baseline − escrow) / baseline; "not defined" when the denominator is 0.

## What the results do and do not establish
* They show the **rules work as specified** on synthetic data and that the escrow **removes specific manual hand-offs** in the modelled process.
* They do **not** show real-world time, cost or risk savings: durations are assumptions, n is small, there are no real banks
  or users, and there is no empirical open-account dataset.
* Fewer steps ≠ better overall. Pre-funding moves the financing burden from exporter to importer (see `charts/financing_burden.png`).
* Peer feedback (proposal §7.6) is a separate, human-collected study: see `peer_feedback_protocol.md`. No responses are included unless real.
