# Conceptual e-HKD extension (proposal §6.3)

**Purpose.** Illustrate the *all-or-nothing* principle when commercial-bank money (tokenised deposits) and
central-bank money (an e-HKD-style wholesale CeBM leg) must move together.

**Scenario.** After an escrow release, the exporter's claim is moved from Bank H to Bank O:
* **Leg A (commercial-bank money):** exporter@BankH → BankH redemption; BankO issuance → exporter@BankO.
* **Leg B (central-bank money, conceptual):** BankH CeBM → BankO CeBM.

**Mechanism.** `tradeescrow/ehkd.py`: a two-phase-commit coordinator. PREPARE reserves funds on each ledger → a durable
COMMIT decision → COMMIT all legs (with retry); any PREPARE failure → ABORT all; a coordinator crash before the decision → recovery aborts all.

| Case | Outcome (actual run, `results/ehkd_results.csv`) |
|---|---|
| success | COMMITTED_BOTH |
| cebm_insufficient | ROLLED_BACK (neither leg changed) |
| deposit_leg_refused | ROLLED_BACK |
| crash_before_decision | ROLLED_BACK |
| transient_commit | COMMITTED_BOTH after retry |

All 5 cases satisfy all-or-nothing, supply conservation on both ledgers, and no leftover reservations.

**Not implemented / not claimed.** No real e-HKD; no HKMA, EnsembleTX or mBridge connection; no legal settlement finality;
no real multi-ledger atomicity (both "ledgers" live in one process); no FX; no central-bank operation; no regulatory approval.
**Context (as of 2 Nov 2026):** HKMA announced that EnsembleTX supports 24/7 interbank settlement of tokenised-deposit transactions
in tokenised CeBM, with 12 participating banks and 20 industry pioneers [HKMA press release, 2 Nov 2026]. This is real-world
context for the design direction, not evidence that this prototype is compatible with it.
