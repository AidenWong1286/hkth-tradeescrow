# Final presentation — speaker script

Slides 1–16 are the talk (Part 3 = slides 9–12, Wong Ho Ming); slides after 16 are backups. Confirm the slot length with the instructor.

_Generated from the deck's speaker notes by scripts/export_speaker_notes.py._

## Slide 1: (untitled)

(20 s) Title. At the interim we showed that the prototype runs. Today we answer the research question: does conditional escrow make HK–Thailand settlement safer and more auditable, and what does it cost? Four parts: why escrow, the design principles, the evidence, and our verdict.

## Slide 2: (untitled)

(40 s) At the interim we showed the prototype running. Since then we did three things. First, an independent review found a real flaw: the ledger page showed every account to every role, even though all 47 tests passed. We fixed it and added 30 tests. Second, we built a proper evaluation: five hypotheses and a fair comparison. That cut our own efficiency claim from 57% to 28.6%. Third, we measured the cost we had ignored: who has to fund the escrow.

## Slide 3: (untitled)

(45 s) The interim compared escrow only with open account. That is an unfair comparison: banks already sell a safe product, the letter of credit. Read the rows: escrow gives the exporter L/C-like certainty, replaces manual document examination with machine matching plus human review, and leaves one shared audit trail. But look at the red dot: the importer must fund in cash up front. That trade-off is what Part 4 measures.

## Slide 4: (untitled)

(40 s) Why build this at all, if HKMA is already tokenising money? Because the programmes solve different layers: data (CargoX), money (Ensemble, e-HKD), and interbank rails (EnsembleTX, mBridge). None of them, as publicly described, holds funds against trade conditions and routes exceptions to people. That missing middle layer is what we prototyped.

## Slide 5: (untitled)

(35 s) Our research question splits into five hypotheses, each with a test that could fail. H1 efficiency, H2 no unsafe release, H3 exceptions go to people, H4 auditability without over-sharing, and H5 — the uncomfortable one — the cost of pre-funding must be measured, not ignored. Part 3 tests them; Part 4 gives the verdicts.

## Slide 6: (untitled)

(45 s) The core design problem is the oracle problem: code cannot see a ship. So we made the trust boundary explicit. On the left, three accountable parties issue attestations. The engine can verify that an attestation is for this trade, is the latest revision, is fresh, and comes from the right role. It must trust that the goods were really loaded and the documents are genuine. That is why every attestation carries an issuer, a trade ID, a digest and an expiry — and why the engine re-checks them at the moment of release.

## Slide 7: (untitled)

(50 s) At the interim we listed the seven guard conditions. Here is why each exists. Each row is an attack someone could try, the check that stops it, and the named test that actually tried it. For example: get documents approved, then quietly revise the invoice — the approval is pinned to a digest, so the revision voids it (NC-05). Or clear a compliance hold without re-screening (NC-11). All seventeen attempts were refused and the money did not move.

## Slide 8: (untitled)

(40 s) Beyond the gates, we specified five invariants that must hold after every command, whatever happens: money is conserved, nothing executes twice, anything not explicitly allowed is refused, each role sees only its own data, and every command — accepted or refused — is chained so tampering is detectable. The bottom line of each card is how we checked it. The state diagram is in backup B2.

## Slide 9: (untitled)

(2–3 min) LIVE DEMO — run: python -m ui_flask.app. Before starting, point at A (lifecycle), B (release guard) and C (ledger line) on the screen so the audience knows where to look.
1) As Bank H ops, TC-001 Auto-play: the guard turns green, one release, supply unchanged.
2) Switch to Regulator, press Try to release funds: RBAC_DENIED, and show the refusal in the journal — the regulator can see but never move money.
3) TC-002: invoice says HKD 245,000 against a 250,000 contract → Under Review; exporter corrects, reviewer revalidates, fresh screening, release.
4) TC-003: watchlist hit → Frozen; try refund → refused.
Fallback: recorded video, then backup B6.

## Slide 10: (untitled)

(60 s) Four kinds of evidence, each answering a different doubt. One: the suite — 77 tests, 30 of them added after the interim to log in as every role and check every page. Two: we attacked the release directly seventeen ways — stale screening, revised invoice, regulator pressing release — all refused, money unchanged. Three: a random stress test — 5,312 random commands from any role across 200 trades; 2,206 were accepted and the trades really moved — 57 released, 64 frozen, 30 refunded — and after every one of 5,935 steps money was conserved and nothing was paid twice. Four: would our tests even notice a bug? We planted fourteen; thirteen were caught, and the survivor is redundant. Margin note: our own tests, synthetic data.

## Slide 11: (untitled)

(60 s) Our most useful lesson: three times, a green result was wrong. One — the leak. At the interim, all 47 tests passed, yet the ledger page showed every account to every role, because no test logged in as a role and looked at the page. An independent review caught it; we moved the access rule server-side and added 30 tests that check every participant on every page. Two — our bug counter said 14 out of 14 because a missing file made every planted bug crash the tests; the honest number is 13. Three — in final review we found the random stress test had been testing nothing since the 8 November fix: every command errored and was counted as refused. Fixed, it now runs 2,206 accepted commands with zero violations. The lesson: test the tests.

## Slide 12: (untitled)

(50 s) Instead of ticking boxes, we place each verdict on an evidence ladder. On the left, the assumptions our models rest on. H1 efficiency and H5 cost sit on the Modelled rung — they are only as good as those assumptions. H2, H3 and H4 sit on the Simulated rung: we actually executed them on the prototype. And the Measured rung is empty — on purpose. No hypothesis has real-world evidence yet; getting there is the next step. Part 4 now looks at H1 and H5 more closely.

## Slide 13: (untitled)

(45 s) H1 in detail. Our first figure said escrow removes 57% of manual settlement tasks. That was unfair: the baseline ends when the Thai bank credits the exporter, but our prototype stops earlier, at Bank H. When we add the steps the escrow would still need to reach the Thai bank, the reduction is 7 to 5, about 29%. Smaller, but the direction holds in all three scenarios. That is the number we stand by — and it is still a model, not a measurement.

## Slide 14: (untitled)

(45 s) H5 in detail. Each row is a timeline from contract. Red is the exporter shipped but unpaid and unsecured; teal is the importer's cash committed. Under open account with a 30-day term, the exporter is exposed for 37 days. Under escrow, the exporter's risk drops to zero — but the importer's cash is locked for 7.5 days instead of 2.5. So escrow is not free efficiency; it is a risk transfer. A real product would need a bank to finance or pay interest on the escrow balance.

## Slide 15: (untitled)

(45 s) Instead of a list of limitations, here is what would have to be true for this to work in the real world. Attestations must be honest — that needs signed electronic bills of lading or CargoX-type data. Settlement must be final across the border — that needs an interbank leg such as EnsembleTX. The legal status of tokenised escrow needs an opinion in both jurisdictions. Someone has to finance the wait. And honestly: a single database could run our rules; a shared ledger only adds value with independent bank and regulator nodes.

## Slide 16: (untitled)

(30 s) Our answer is a qualified yes. Safer and auditable: supported. More efficient: somewhat, about 29% fewer manual tasks, as a model. Not free: it moves the financing cost to the importer, and its real-world value depends on trusted data, settlement finality and law. Next steps are on the slide. Thank you — questions. Backups B1–B9 hold the full diagrams, permissions, the e-HKD leg and sources.

## Slide 17: (untitled)

_(section divider)_

## Slide 18: (untitled)

_(section divider)_

## Slide 19: (untitled)

_(section divider)_

## Slide 20: (untitled)

_(section divider)_

## Slide 21: (untitled)

_(section divider)_

## Slide 22: (untitled)

_(section divider)_

## Slide 23: (untitled)

_(section divider)_

## Slide 24: (untitled)

_(section divider)_

## Slide 25: (untitled)

_(section divider)_

## Slide 26: (untitled)

_(section divider)_
