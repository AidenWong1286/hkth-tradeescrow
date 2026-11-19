# Known issues and open items (as of 2026-11-08, after the independent audit revision)

## Fixed in this revision (see CHANGELOG.md)
- **UI data-access bypass (was HIGH).** Ledger & integrity pages in both UIs listed every account and the full journal
  for every role. Now served through `views.ledger_view` (Bank H full; importer/exporter own accounts and own-trade
  events; regulator and Bank O metadata only; logistics/customs denied and logged). HTTP tests: `tests/test_ui_access.py`.
- **UI actor identity.** `run_action()` used fixed default principals (e.g. importer #1 for *Create & fund escrow*,
  the document/screening services, the contract engine). Every UI action now runs as the participant selected in the UI;
  e.g. importer #2 pressing *Create & fund escrow* is refused with NOT_TRADE_BUYER and journalled under `u_importer_02`.

## Still open
1. **Streamlit full click-through.** Package installs are blocked in the build environment. The team reports a
   successful local launch (8 Nov 2026); a recorded walk-through of TC-001/002/003 and the ledger tab for each role
   on the presentation laptop is still pending. The stub smoke test exercises every participant. The Flask console
   is verified by browser click-through, screenshots and HTTP tests and remains the fallback demo.
2. **Peer feedback not collected** (needs real participants; report §7.4 holds a placeholder).
3. **Individual reflections** must be written by each member (report Appendix A placeholders).
4. **AI declaration** (Appendix F) must be checked by the team against actual tool use; the academic-honesty declaration must be signed.
5. **Demo security model.** "Act as" is role impersonation, not authentication; the Flask app keeps one in-memory
   ledger per process (single operator). Do not expose it beyond localhost. Operator controls are loopback-only and
   can be disabled with `TRADEESCROW_DEMO_CONTROLS=0`.
6. **Mutation M11 survives** (removing the optimistic `version` check in `_set_state`). `BEGIN IMMEDIATE` already
   serialises writers and TC-019 still passes; redundant defence in depth, documented rather than "fixed".
   Run 1 detected 11/14; two genuine gaps (M02, M06) were closed (run 2: 13/14). The harness now refuses to score
   mutants if the unmutated sandbox fails (it previously could not import the new UI tests and would have reported 14/14).
7. **Process comparison scope.** The prototype ends at a Bank H release; the baseline ends with a Bank O credit.
   The matched-scope variant (M-31…M-34) uses hypothetical steps that are not implemented.
8. **Clean-machine rebuild.** `package.json`, a project-local theme script and a plain LibreOffice route remove the
   dependency on the AI sandbox, but a rebuild on a student laptop has not yet been performed. No lockfile is committed
   because package installs were blocked here; run `npm install` once to create one.
9. UI actions advance the simulated clock by 30 minutes each (illustrative), so UI timestamps differ from the scripted scenario logs.
10. ISO 20022 fields in the RELEASE event are "inspired" mock fields, not schema-validated messages.
11. Presentation durations not confirmed by the course outline; decks assume ~5 min (interim) / ~12 min (final).
