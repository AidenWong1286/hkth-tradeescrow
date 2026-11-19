# Demo plan and fallback

**Setup (before class, on the presentation laptop):** `pip install -r requirements.txt`; start `python -m ui_flask.app`
(or `streamlit run ui_streamlit/streamlit_app.py`); open http://127.0.0.1:5050; choose "TC-001 clean trade"; click
*Reset ledger with this fixture*. Keep `results/screenshots/` open in a second window. Record a 60–90 s screen capture
of Demo 1 as a backup (not yet recorded; do not substitute generated images).

**Demo 1 (2 min):** *Auto-play* → stepper shows Released; release guard shows shipment/documents/KYC ✔ and
TERMINAL_STATE (already released) → switch to *Regulator* → metadata-only audit trail → press *Try to release funds
(forbidden)* → red RBAC_DENIED banner and a REJECTED event in the trail → open *Ledger & journal* as Regulator
(metadata only) and as Logistics (ACCESS_DENIED).

**Optional (20 s):** act as *Hong Kong importer — u_importer_02* and press *Create & fund escrow* → NOT_TRADE_BUYER,
recorded under u_importer_02 (shows actions run as the selected participant).

**Demo 2 (1.5 min):** select "TC-003 …" → *Reset* → *Auto-play*, or act as each role in turn; point at FREEZE,
the refused SETTLE (ESCROW_FROZEN), the refused refund (ACTIVE_HOLD), the clearance, the refused release before
re-screening (PRE_RELEASE_KYC_MISSING) and the final RELEASE.

**Fallback:** final slides F6–F7 (real screenshots), `results/screenshots/*.png` (24 captures, 8 Nov 2026) and
`results/events/*.jsonl`. **Reproducibility, if asked:** `python -m pytest -q` (77 tests, about 1 s).
