# HK–TH TradeEscrow

**A tokenised-deposit escrow prototype for Hong Kong–Thailand cross-border trade finance**
CUHK FTEC3002 (2026–27 Sem 1) · Group 1 · low-fidelity simulation, **synthetic data only**

> No live bank, tokenised deposit, e-HKD, EnsembleTX, mBridge, blockchain, KYC/AML engine or customs
> system is connected. The smart contract is simulated by a Python service. KYC/AML and document
> results are simulation inputs, not regulatory clearance.

## What it does

An importer pre-funds an escrow of simulated tokenised deposits (HKD, integer cents). The escrow
releases to the exporter **only** when three off-chain attestation gates pass, all of them current:

1. **Shipment.** The logistics attestation is for *this* trade's shipment.
2. **Documents.** Contract, invoice, bill of lading and customs declaration match field by field, on the *latest* revisions.
3. **KYC/AML.** The creation check passed, a fresh pre-release check passed (48-hour window), and no compliance hold is active.

The escrow has six states: **Created · Pending · Under Review · Frozen · Released · Refunded/Terminated**
(15 permitted transitions; everything else is rejected). Seven roles act through server-side RBAC:
importer, exporter, Bank H (operations and compliance), Bank O, logistics, customs and regulator.
The regulator has a read-only, metadata-only audit view. Every accepted *and rejected* command is
written to a SHA-256 hash-chained journal.

## Quick start (Python ≥ 3.11)

```bash
pip install -r requirements.txt
python -m pytest -q                       # 91 tests (TC-001..TC-024, e-HKD, invariants, UI access control, console)
python scripts/run_experiments.py         # regenerates results/ (≈15 s); on Windows set PYTHONUTF8=1 first
python -m ui_flask.app                    # Flask console -> http://127.0.0.1:5050  (intro page: /intro)
streamlit run ui_streamlit/streamlit_app.py   # the proposal's Streamlit UI (same engine)
python scripts/make_diagrams.py           # BPMN XML + PNG, state machine, architecture
```

**The Flask console** (redesigned 19 Nov 2026) shows one escrow as a trade corridor: importer vault →
escrow ring (the 7-check release guard) → exporter vault, a lifecycle map, a hash-chained journal and a
role lens. Animations only replay results the engine has already journalled. Use the player at the bottom
to replay TC-001/002/003 step by step (Space plays, **C** = cinema mode); the top-right switch toggles
light/dark. Operator-only demo controls include an AML hit, clock +24 h and a journal-tamper demonstration.

Screenshots (needs `pip install playwright` and Microsoft Edge; console running):

```bash
python scripts/capture_walkthrough.py     # 21-screen walkthrough -> results/screenshots/walkthrough/
python scripts/capture_screenshots_v2.py  # deck/report shots, light + dark -> results/screenshots/v2/
```

Report and final deck (Node ≥ 20, LibreOffice, poppler-utils):

```bash
npm install                               # pinned versions in package.json
bash scripts/rebuild_all.sh               # tests → results → diagrams → charts → report → deck, in order
```

See **CLAUDE.md** for the file map and the checklist of what to update when the UI or a function changes.

**Demo scope.** The Flask console is a single-operator localhost demo. "Act as" is role impersonation,
not authentication; every action runs as the selected participant and is authorised by the engine, and
every page that shows ledger data uses the role projections in `tradeescrow/views.py`. Operator simulation
controls (`/sim/*`) are served to loopback clients only; set `TRADEESCROW_DEMO_CONTROLS=0` to disable them.

Course documents (the course outline and the submitted proposal) and generated documents with student IDs
(report, decks, cover images) are deliberately **not** in this repository; they are rebuilt by the scripts.
Student IDs are read from `team.local.json` (git-ignored; copy `team.example.json` and fill it in); without it the
cover and slide footers show names only.

## Repository map

| Path | Contents |
|---|---|
| `tradeescrow/model.py` | States, roles, permission table, transition table |
| `tradeescrow/escrow.py` | **EscrowService**: commands, release guard, token accounting, journal, integrity check |
| `tradeescrow/offchain.py` | Simulated document matching and KYC/AML screening modules |
| `tradeescrow/views.py` | Role projections and role-filtered audit export |
| `tradeescrow/ehkd.py` | Conceptual e-HKD two-leg atomic settlement (2-phase commit, rollback) |
| `tradeescrow/process_model.py` | Baseline and proposed process models, the single source for BPMN and metrics |
| `tradeescrow/scenarios.py`, `ui_actions.py` | Reproducible scenario scripts; shared UI action catalogue |
| `fixtures/base_fixture.json` | Synthetic parties, trade, documents (fixture FX-2026.11.07-v1) |
| `tests/` | pytest suite |
| `ui_streamlit/`, `ui_flask/` | Two UIs over the same engine |
| `diagrams/` | `baseline.bpmn`, `proposed.bpmn` (BPMN 2.0 + DI), PNG renders, state machine, architecture |
| `docs/` | Pseudocode (`TradeEscrow_pseudocode.sol`), domain model, evaluation method, e-HKD note, limitations, peer-feedback protocol, known issues |
| `results/` | Evidence bundle (see `results/README.md`) |
| `requirements/` | Traceability, test cases, progress tracker, evidence and public-claims registers |
| `interim/`, `report/`, `presentation/` | Deliverables |

## Verification status (run of record: see `results/run_manifest.json`)

| Check | Result |
|---|---|
| pytest | 91 / 91 pass (incl. 30 UI access-control / actor-identity tests and 14 console tests) |
| Flagship scenario assertions | 63 / 63 |
| Unsafe release attempts blocked | 17 / 17 (positive control releases) |
| Role-visibility rules obeyed | 63 / 63 (core projections) + HTTP tests for the ledger page, export and operator controls |
| Random command sequences (200 trades, 5,312 commands, seed 3002) | 0 invariant violations in 5,935 checks |
| Mutation analysis (seeded defects detected) | 13 / 14 (M11 redundant under serialised transactions; see docs/known_issues.md) |
| e-HKD all-or-nothing cases | 5 / 5 |

Streamlit was **not installable in the build sandbox**; its logic is smoke-tested against a stub for every
participant (`scripts/dev/streamlit_stub_smoke.py`). The team reports a successful local launch (8 Nov 2026);
a full recorded click-through of all workflows is still pending (see `docs/known_issues.md`).

Process-comparison numbers (7 → 3 manual tasks; 7.0 → 0.5 simulated days) are a **team-defined process model
with assumed durations, not measured industry savings**; a matched-scope variant (7 → 5) is in `results/metrics.csv`
(M-31…M-34). See `CHANGELOG.md` for the post-audit revision.
