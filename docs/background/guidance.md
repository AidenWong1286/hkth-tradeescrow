# HK–TH TradeEscrow — MASTER PROJECT EXECUTION GUIDANCE

**Course:** FTEC3002 — Introduction to Financial Infrastructure, CUHK, 2026–27 Semester 1  
**Team:** Group 1 (four members; individual responsibility assignments are not specified in the submitted proposal)  
**Document type:** Implementation and evidence specification for collaborating research, engineering, evaluation, writing and presentation models  
**Version:** 1.0 · 7 November 2026 · Planning guidance, **not** an official CUHK-issued document  
**Single authoritative project baseline:** `FTEC3002_Group_1_Project_Proposal.docx` (the **10-page version most recently uploaded and identified by the team as officially submitted**). Older proposals, revised drafts and 9-page alternatives must **not** be merged into the baseline.  
**Second authoritative input:** `FTEC3002 Course Outline (2026-27) v1.2(1).pdf`.  
**Optional inspiration only:** `Group 6(update) (1).pptx` — an unrelated group's interim-update example. Its architecture, metrics, invented dashboards and project decisions are **not** evidence or requirements for Group 1.

> **Operating instruction for every execution model:** Read this entire file and the two authoritative source documents before implementing. Do not silently change the approved project scope. For any uncertain item, record an assumption, its effect and the required verification. Deliver working artefacts and reproducible evidence, not only attractive designs or plausible-sounding results.

---

## How to interpret this guidance

- **[COURSE]** = express requirement or deadline in the CUHK course outline.
- **[BASELINE]** = commitment in the team's officially submitted proposal.
- **[RECOMMENDATION]** = proposed implementation choice to make those commitments coherent, testable and feasible. It is **not** a grading rule issued by CUHK.
- **[EVIDENCE]** = material that must exist before an implementation, performance claim, milestone or slide can be represented as completed.
- **[OPTIONAL]** = enhancement that must never displace the core scope or deadlines.

### The official assessment and near-term calendar

| Item | Official date / weight | How to treat it |
|---|---|---|
| Project Proposal | 25 Sep 2026, 23:59; **5%** | Already officially submitted; preserve its scope. |
| Interim Project Update 1 | 26 Oct 2026 | Course timetable; historical milestone, not evidence that an implementation was completed. |
| **Interim Project Update 2** | **9 Nov 2026** | Short class update; listed as **2% included in Class Participation**, not an additional stand-alone 2% of the 100% total. |
| **Final Project Report** | **19 Nov 2026, 23:59; 20%** | Earliest remaining major graded deliverable. |
| **Presentation Slides** | **22 Nov 2026, 23:59** | Separate slide-submission deadline; no separate slide weighting is specified in the outline. |
| **Project Presentation** | **24 Nov or 1 Dec 2026; 15%** | Exact group allocation and permitted presentation duration must be checked with instructor/Blackboard; neither is provided in the course outline. |

**[COURSE]** Project Proposal (5%), Project Presentation (15%) and Project Report (20%) together account for **40%** of the course. The broader assessment also includes class participation (10%) and two quizzes (25% each). The outline states **no late submissions will be accepted**. The report must **not exceed 15 pages**, **excluding the cover, table of contents, executive summary, appendices, figures and references**. The report must include **individual self-reflections**. The outline also requires appropriate academic-integrity declarations and permits generative AI under **Approach 3: explicit acknowledgement and proper citation**. [C1]

**[COURSE]** The intended learning outcomes include understanding financial infrastructures, infrastructure-related risk, identifying shortcomings in early implementations, designing improvements and demonstrating planning, teamwork and communication. The group-project process calls for design, prototyping, experimentation, evaluation, instructor/peer feedback, presentation and a final analytical report. The outline provides broad grade descriptors (e.g. A-level work demonstrates superior analysis and skilful application of knowledge), **not** a quantitative project-specific marking rubric. Do not invent a rubric or claim guaranteed marks. [C1]

### The four interlocking work packages

1. **Part I — Interim Project Update:** an honest evidence-backed progress snapshot on/for 9 November, aiming for roughly **70–80% of the design-and-experimentation workstream demonstrably complete**, not a fake percentage.
2. **Part II — Project Design and Experimentation:** the **full** specified low-fidelity prototype, reproducible scenario tests, controls, evaluation and evidence package.
3. **Part III — Final Project Report:** a submission-ready explanation and critical assessment **based on the real artefacts and observed outcomes**.
4. **Part IV — Final Presentation Slides:** a concise, convincing demonstration of the problem, solution, live workflow, measured findings, limitations and answers to likely questions.

**Dependency rule:** Part II produces all evidence. Part I uses a dated snapshot of Part II. Parts III and IV must only state results verifiable in Part II. The presentation may simplify but **must not change** the tested outcomes, sample sizes or scope.

### Non-negotiable boundaries from the submitted proposal

**Project question:** Can a simulated **pre-funded smart-contract escrow with tokenised deposits** improve efficiency, traceability, transparency and auditability of Hong Kong–Thailand trade-finance settlement while retaining meaningful compliance controls?

**What the system IS:** A **low-fidelity, synthetic-data, permissioned-DLT-style decision and settlement workflow prototype** combining a simulated ledger, a smart-contract-like state machine, off-chain shipping/document/KYC–AML attestations, role-limited interfaces, three primary scenarios, BPMN process maps, measured comparison to an open-account baseline and a **conceptual** e-HKD atomic-settlement illustration. [P1]

**What it is NOT:** a live blockchain, a Solidity deployment, a bank-connected payment rail, an actual tokenised deposit issued by a bank, a real e-HKD or mBridge integration, a commercially certified KYC engine, real customs authorisation, genuine AML clearance, a production legal escrow, or proof of genuine cross-border settlement. No live accounts, passwords or personal financial data. [P1]

**Always distinguish the three currencies/claims:**

- **Simulated tokenised commercial-bank deposit** = a digital representation of a claim on a commercial bank in a **mock** ledger.
- **Simulated central-bank-money leg** = an **e-HKD / tokenised CeBM concept** used in an extension; this is legally and operationally different from a commercial-bank claim.
- **Trade payment denomination** = an explicit simulated currency (for the core demo use **HKD only** unless a separately documented conversion mock is added). A Thai bank appearing on screen must not create the impression that actual cross-border FX and bank-to-bank settlement occurred.

**Potential weakness to address explicitly:** The comparison is **open account after shipment versus pre-funded escrow before shipment**. Faster automated release does **not** by itself establish lower end-to-end cost or faster overall payment once pre-funding, liquidity tie-up, bank onboarding, disputes and compliance are counted. Report both benefits and trade-offs.

---

# PART I — INTERIM PROJECT UPDATE (70–80% PROGRESS SNAPSHOT)

## I.1 Purpose, date and truth-in-reporting rule

**Purpose:** Show the instructor the concrete progress towards a working project, expose technical rationale, demonstrate at least one complete customer-visible transaction journey and gather feedback before the graded report and final presentation. This is **not** a second project proposal or a sales pitch for functionality that does not yet exist.

**[COURSE]** Interim Update 2 is scheduled on **9 November 2026**, with the update component included in class participation. The course document does **not** stipulate number of slides, speaking duration, video length, or a 70–80% completion threshold. The **70–80%** target is a **team planning objective supplied by the user**, not an official grading condition. [C1]

**Critical:** If the team completes 100% of Part II before the update, report the honest actual state. Do not deliberately hide finished work or relabel complete work as 75%. If only 45% is operational, report 45% with dated evidence and a recovery plan. A professional progress report separates **completed / demonstrable / validated / in progress / not started**.

## I.2 Evidence-based 75% milestone model (team-defined)

Score each weighted workstream as `0` (not started), `0.5` (partially demonstrated), or `1.0` (definition of done met). Calculate progress as `sum(weight × completion factor)`. This measures **planned deliverables**, not lines of code, graphical polish or hours worked.

| Workstream and objective evidence | Weight | Target at interim |
|---|---:|---|
| A. Frozen requirements, system architecture, role map and assumptions register | 10 | 10 |
| B. Two traceable BPMN maps (baseline and proposed flow) | 10 | 10 |
| C. Synthetic fixture schema, document checks and off-chain attestation modules | 10 | 10 |
| D. Executable escrow state machine, balance conservation and idempotency | 20 | 20 |
| E. Ledger/event history and usable role-specific views | 15 | 15 |
| F. Three primary scenario smoke demonstrations with captured logs | 10 | 10 |
| G. Complete evaluation study, extended test suite and sensitivity checks | 10 | 0 |
| H. Peer feedback collection and analysis | 5 | 0 |
| I. e-HKD atomic-settlement concept demonstration with safeguards | 5 | 0 |
| J. Final reproducibility, deployment polish and evidence export | 5 | 0 |
| **TOTAL** | **100** | **75** |

**Completion for A–F must be substantiated** by design files, running software and scenario captures. A beautiful slide or screenshot without working behaviour cannot earn the corresponding completed workstream. This is an internal progress framework and should be labelled as such in slides.

## I.3 Exact implementation sequence before the update

**Step 1 — Freeze the requirements.** Create `requirements_traceability.csv`; include every baseline promise in Sections 4–8 of the proposal, mapped to a component, test ID, evidence filename and current status. Agree definitions of `Released`, `Frozen`, `Under Review` and `Refunded/Terminated`. Confirm the demo's one-currency assumption.

**Step 2 — Draw the workflow.** Complete BPMN (1) traditional open account and (2) proposed pre-funded escrow with swimlanes for importer, exporter, banks, logistics/customs and compliance; record what tasks are modelled and what are assumed. In the redesigned map, show funding **before shipping**, dual KYC/AML control points, document verification, decision gateways, exception human review, and final release or refund. BPMN 2.0.2 is the appropriate formal notation reference [R8].

**Step 3 — Implement only genuine functional vertical slices.** Use the same service layer for the UI and all tests; do not hard-code screenshots. Implement `create escrow → lock balance → simulated shipment attestation → document check → compliance check → release → audit history`. Add a mismatch and an AML alert branch with working state-change controls.

**Step 4 — Demonstrate a full normal journey and two exceptions.** Save timestamped screenshots or a local screen recording and a machine-readable event export for each. Capture state before/after and actor who triggered each transition. No unexplained state jump.

**Step 5 — Prepare measured but carefully scoped initial figures.** May show **test pass counts** and **observed simulated workflow steps** after running the code; do **not** show percentage time savings, actual financial value created or near-perfect accuracy until the comparator is reproducible and test population is defined.

**Step 6 — Hold a dry run.** Re-open the app from a clean environment, reset the synthetic fixtures and replay the three sample cases without developer intervention. If it fails, lower the reported status and describe the blocker.

## I.4 Interim update recommended story (6–8 slides; adjustable to actual allotted time)

The course does not specify an exact interim slide limit. For a short update use **7 main slides + optional appendix**, prioritising demonstration over general literature.

| Slide | Working title | Essential evidence / assertion |
|---|---|---|
| 1 | **HK–TH TradeEscrow — What is already working?** | Team, research question, one-sentence scope and dated progress claim with evidence basis. |
| 2 | **The problem and our constrained design choice** | Open account vs pre-funded escrow; one succinct pain-point visual; clarify payment versus trade finance availability. |
| 3 | **System architecture and trust boundaries** | Diagram with actors, app/engine, off-chain validations, mock ledger, audit view, money flows; no fictional deployed chain. |
| 4 | **The core escrow state machine** | Six official states, release guard, review/freeze/refund paths; one meaningful rule excerpt. |
| 5 | **Evidence from the running prototype** | Real screenshots or live demo: creation, document validation, role view, ledger timeline. Dated build/revision. |
| 6 | **Three scenarios: early results** | Actual test table: normal, mismatch, AML, expected vs actual, evidence ID, and test status. |
| 7 | **Progress, blockers and next steps** | Weighted progress with definitions; remaining evaluation, feedback and e-HKD extension; specific milestones before 19 Nov. |

**[OPTIONAL]** One backup slide on data provenance, a failure-handling sequence or exact acceptance metrics. Do not invent a poll, survey, bank interview or performance chart. If a module is a mock or is not yet wired, label it prominently.

### Recommended live demonstration (not a fixed course requirement)

**Demo A (normal):** select `TC-001`, show importer balance before/after lock, choose logistics role to attest shipment, upload/select compatible synthetic documents, choose compliance role to grant signed mock clearance, trigger `Release` through guarded action, show exporter credit and end-to-end audit log.

**Demo B (mismatch):** select `TC-002`, demonstrate field-level mismatch, transition to `Under Review`, blocked release and logged reviewer action. Do not imply a document mismatch is itself an AML alert.

**Demo C (AML):** select `TC-003`, trigger a fresh compliance alert, show `Frozen` and a denied release/refund until authorised review; demonstrate evidence trail and explicit hold (or conditional authorised resolution if actually implemented).

**What to say about the app:** “This is an executable, rule-driven simulation with synthetic data; commercial-bank token and e-HKD settlement are not live.”

## I.5 Interim quality gates and handoff

Before calling this update ready, another model/person should check: (a) citations and screenshots point to the correct data; (b) an app operation changes persistent application state, not merely UI text; (c) no fake numbers; (d) the state machine enforces balance conservation and blocks invalid release; (e) both normal and exception paths can be replayed; (f) the recorded progress percentage reconciles to the weighted table; (g) screenshots are from the version being demonstrated; and (h) presentation time is obtained from instructor rather than guessed.

**Interim output package (recommended):** `interim_update.pptx`, `interim_update.pdf`, `demo_video.mp4` or runnable demo URL (optional), `snapshot_2026-11-09.md`, `progress_evidence.csv`, `architecture_v1.svg`, `baseline.bpmn`, `proposed.bpmn`, test exports and `known_issues.md`.

---

# PART II — PROJECT DESIGN AND EXPERIMENTATION (COMPLETE THE PROJECT CORE)

## II.1 Design objective, hypothesis and testable claims

**Research question (binding):** Whether the proposed smart-contract escrow can improve trade-finance settlement processes in a simulated Hong Kong–Thailand corridor while preserving compliance, auditability and exception control. [P1]

**Research hypotheses to evaluate; do not presuppose success:**

- **H1 (workflow):** Given the same declared workflow assumptions, the proposed escrow may reduce the number of manual tasks and time spent in the specified settlement segment of a transaction.
- **H2 (control correctness):** Funds cannot be released when shipping, document or current KYC/AML attestations are missing, failed, expired or revoked.
- **H3 (exception safety):** Mismatch leads to review; AML alert leads to freeze; neither silently releases funds or erases evidence.
- **H4 (audit):** Authorised reviewers can reconstruct key events and responsibilities from the event history, without access to unrelated commercial documents.
- **H5 (trade-off):** Pre-funding may increase liquidity lock-up or alter risk allocation versus open account; these costs must be acknowledged rather than omitted.

The core work is **not** a prediction model or a fraud-scoring engine. A sophisticated analytics dashboard, genuine bank API, chain deployment or AI assistant is **not required** by the approved proposal; add none until the core has passed its acceptance criteria.

## II.2 Trust model, participants and responsibility boundary

### Seven business participants defined by the proposal

| Participant | Responsibility within simulation | Permitted evidence/action | Not authorised to do |
|---|---|---|---|
| Hong Kong importer | Create trade/escrow and provide simulated funding | Create, view own trade, fund, acknowledge dispute | Self-approve AML or force release |
| Thai exporter | Review trade, prepare shipping documents, track receipt | View own trade, submit documents, receive released tokens | Edit bank clearance or shipper confirmation |
| Hong Kong Bank H | Mock issuing/escrow bank and control owner | Verify funding, approve specified reviews, administer role assignment | Bypass all compliance gates without evidence |
| Thai Bank O | Mock receiving-bank stakeholder | View permitted escrow/settlement status, post mocked receipt acknowledgement if modelled | Assert real THB credit or actual cross-bank finality |
| Logistics Provider L | Source of synthetic shipment attestation | Confirm shipment against a shipment ID | Change invoice amounts or KYC statuses |
| Customs Authority C | Source/validator of synthetic customs attestation/record | Provide scoped customs confirmation | Approve fund movement outside defined rules |
| Regulator R | Read-only audit and compliance oversight in prototype | View event trail, flags, timestamps and scoped data | Edit transaction, issue fund transfers or see all confidential records by default |

**Off-chain services** (document matching, mock KYC/AML, attestation issuance, identity/RBAC) are **software modules**, not additional real-world parties. The app must show an attestation's source, issue time, subject, status and version. In reality commercial bank KYC, regulators and customs have distinct statutory and operational responsibilities; this simulation must not imply that a regulator routinely clears individual payments in real time.

### Recommended architecture (realistic low-fidelity implementation)

```text
Synthetic fixture files / importable sample trade
                 │
                 ▼
      Streamlit UI + role selector
                 │   (server-side authorisation)
                 ▼
         Escrow service layer
            │        │
            │        ├── Simulated document-matching service
            │        ├── Simulated logistics & customs attestations
            │        └── Simulated KYC/AML rules service
            │
            ├── Deterministic state-transition validator
            ├── Mock token accounting / fund locking
            ├── Append-only event journal + hash chain (optional)
            ├── Role-filtered read models / audit projections
            └── Test/export/report pipeline
                        
     OPTIONAL: separate illustrative two-leg atomic settlement
     (e-HKD/central-bank-money mock; no real integration)
```

A shared SQLite database is usually sufficient and makes deterministic replay simple. The prototype may call this a **simulated permissioned ledger**; it must not suggest that an ordinary SQLite table is a deployed distributed consensus network. If a hash chain is included, state it is a **tamper-evident demonstration**, not tamper-proof or an independently governed DLT. For verifiable evidence, ship a script that detects post-hoc event modification.

### Money-accounting model: make claims precise

**[RECOMMENDATION]** Keep the core contract **single-currency synthetic HKD**. Define importer available balance `I`, escrow locked balance `E`, exporter credited balance `X`; an accepted release changes `E → X`, refund changes `E → I`. For each synthetic token-currency ledger, require:

`I + E + X + (other tracked balances) = fixed issued supply`.

Record debit and credit journal entries. All monetary values use integer minor units (cents) to avoid floating-point settlement errors. A Thai Bank O interface can *observe* or *acknowledge* a modelled claim; do not pretend this is actual Thai domestic money or an executable FX trade. Real bilateral credit-risk, redemption, governing law and cross-border cash settlement remain outside scope.

**Exception funds:** For `Frozen`, no automated refund, release or transfer is allowed while an AML hold persists. Only an explicit mock authorised review can clear the hold, and the review must be logged with actor, timestamp, evidence and outcome. `Under Review` is similarly non-releasable until an authorised document-review action succeeds. Refund on a document dispute is possible only after the defined resolution/authorisation path.

## II.3 Canonical data contract (implement consistently in code and tests)

Use these representative schemas; actual code can adapt the language but must keep field semantics.

### Trade record

```yaml
trade_id: TR-001
buyer_id: importer_hk_01
seller_id: exporter_th_01
issuer_bank_id: bank_hk_h
recipient_bank_id: bank_th_o
currency: HKD
amount_minor: 25000000             # synthetic HKD 250,000.00; illustrative only
invoice_id: INV-001
bill_of_lading_id: BL-001
shipment_id: SH-001
customs_declaration_id: CUS-001
escrow_id: ESC-001
created_at: simulated ISO-8601 timestamp
contract_terms: synthetic description and shipment condition
```

### Attestation record

```yaml
attestation_id: ATT-001
trade_id: TR-001
type: SHIPMENT | DOCUMENTS | KYC_AML | CUSTOMS
subject_id: entity or shipment the claim concerns
issuer_role: LOGISTICS | DOCUMENT_VALIDATOR | BANK_COMPLIANCE | CUSTOMS
result: PASS | FAIL | ALERT | PENDING
issued_at: simulated ISO-8601 timestamp
expires_at: simulated ISO-8601 timestamp or null
revision: 1
input_digest: deterministic hash of input fixture, if appropriate
reason_code: e.g. DOC_AMOUNT_MISMATCH / SANCTIONS_FLAG_SIMULATED
review_reference: mock decision ID or null
```

### Event journal record

```yaml
event_id: EVT-000001
trade_id: TR-001
escrow_id: ESC-001
timestamp: simulated ISO-8601 timestamp
actor_id: user/service principal
actor_role: role identifier
operation: CREATE | LOCK | ATTEST | REJECT | REVIEW | FREEZE | RELEASE | REFUND
prior_state: CREATED
new_state: PENDING
reason_code: explicit code
related_attestation_ids: []
amount_minor: integer or null
prev_event_hash: optional deterministic previous hash
current_event_hash: optional deterministic hash
```

All test cases must use stable IDs and run with a documented fixture version, code revision, deterministic clock or seeded timer and an event-export format. Prefer redacted/auditable data by default. Never use actual identity numbers, client names or leaked production datasets.

## II.4 State-machine specification: retain the proposal's **six states**

**[BASELINE]** The official proposal specifies exactly: `Created`, `Pending`, `Under Review`, `Frozen`, `Released`, `Refunded/Terminated`. These labels must appear in the report, UI and testing. Do not silently replace them with a different protocol. [P1]

### Transition table — enforce in the engine, not just in interface text

| From | Trigger / guards | To | Required audit evidence |
|---|---|---|---|
| no escrow | authenticated mock importer funds exactly once; enough available balance; valid terms | Created | CREATE + LOCK with amount and balance entries |
| Created | valid shipment attestation received (funds remain locked) | Pending | attestation ID, timing, issuer |
| Created / Pending | document discrepancy, stale/missing authoritative document or manual dispute | Under Review | mismatch code, doc field names/digests, assigned reviewer |
| Created / Pending / Under Review | compliance ALERT/FAIL, expiry or explicit mock hold | Frozen | reason code, source and denied operations |
| Pending | current shipping PASS + current documents PASS + KYC/AML PASS at required checkpoints + no active holds + authorised command | Released | release guard evaluation + one debit/credit posting |
| Under Review | authorised correction/revalidation; no AML hold | Pending | reviewer ID, corrected evidence version, decision |
| Under Review | authorised termination under simulated dispute rules; no unresolved AML hold | Refunded/Terminated | reason, dual control if configured, refund posting |
| Frozen | authorised mock compliance review clears hold and rechecks required controls | Pending or Under Review | documented reviewer clearance and revalidation |
| Frozen | formal mock hold resolved and termination/refund explicitly permitted under defined simulation policy | Refunded/Terminated | decision reference and refund event |
| Released / Refunded/Terminated | any attempt to issue new release/refund | REJECT | denied operation, reason `TERMINAL_STATE` |

**Invariant rules**

1. Release only if all **three** mandatory releases gates pass with **current, matching, non-revoked** evidence for the right transaction.
2. The first KYC/AML gate must pass at **escrow creation** and the second at **pre-release**. An alert between them must block the release.
3. A FAIL/ALERT never triggers an automatic payout; a missing attestation is not a PASS.
4. No double release, negative balance or refunded-and-released combination; repeated button clicks are idempotent.
5. Every accepted/rejected state-changing request has a timestamped audit record with actor and reason.
6. A role cannot approve its own forbidden action by switching the display view. Permission checks are server-side.
7. Any document correction increments revision and invalidates approvals tied to old content.
8. Terminal outcomes cannot be undone without creating an entirely new independent escrow.
9. A user cannot set an arbitrary state manually in production-like demo mode; transitions run through authorised commands.
10. Human review is explicitly **not** equivalent to automatic self-certification by the smart contract.

### Executable rule sketch (implementation guidance; not a deployed Solidity contract)

```python
def can_release(trade, attestations, escrow, holds, now):
    if escrow.state != 'Pending' or escrow.locked_minor != trade.amount_minor:
        return False, 'ESCROW_NOT_READY'
    if holds.active:
        return False, 'ACTIVE_HOLD'
    if not passes_current('SHIPMENT', trade, attestations, now):
        return False, 'SHIPPING_NOT_VERIFIED'
    if not passes_current('DOCUMENTS', trade, attestations, now):
        return False, 'DOCUMENTS_NOT_VERIFIED'
    if not passes_creation_kyc(trade, attestations):
        return False, 'CREATION_KYC_MISSING'
    if not passes_fresh_prerelease_kyc(trade, attestations, now):
        return False, 'PRE_RELEASE_KYC_MISSING'
    return True, 'OK'
```

The real implementation must additionally use an **atomic database transaction** for guard evaluation, debit/credit posting and event append; concurrency checks and unique command IDs prevent race conditions. A toy pseudocode example alone does not establish that these safeguards are implemented.

## II.5 Reference process flows / BPMN modelling requirements

### A. Traditional open-account baseline (comparison model)

Proposed lanes: **Importer / Exporter / Logistics / Importer Bank / Exporter Bank** (add customs/compliance lanes where modelled). Include: agree trade, exporter ships, prepares commercial documents, logistics confirms shipment, exporter sends documents, importer/bank reviews and authorises payment after shipment, interbank instruction, settlement confirmation and audit record creation. Mark **assumed** durations and manual approvals. This is an abstraction, not a claim that all real open-account transactions follow the same route or that letters of credit and open account are interchangeable.

### B. Proposed pre-funded escrow

Lanes: **Importer → Bank H/escrow engine → Exporter → Logistics/customs → Document validator → Bank compliance → Bank O/view → Regulator/audit**. Include: importer funds before shipment, creation KYC/AML, locked tokens, verified shipment, document matching, fresh release KYC/AML, guarded automatic release, exporter balance credit, event trail and alternative mismatch/AML subprocesses. Any transfer to a Thai commercial bank is conceptually modelled only.

**BPMN quality gate:** consistent start/end events, named tasks, exclusive gateways with explicit branch conditions, subprocesses for review/freeze/refund, pools/lanes and message flow distinctions, numbered step mapping to measurable workflow metrics. BPMN notation basis [R8].

## II.6 Test plan: three flagship scenarios plus edge cases

Every test record must include: ID, synthetic fixture, preconditions, actor operation, expected states, expected balances, expected audit events, actual result, pass/fail, run timestamp and code revision. Tests must be executable without UI clicks through the same service layer.

### Flagship demos — illustrative inputs, **not measured outcomes**

| Test ID | Scenario & synthetic seed | Expected observable behaviour |
|---|---|---|
| TC-001 | Clean HKD 250,000 trade. Shipping PASS, documents PASS, creation and pre-release KYC/AML PASS. | Created → Pending → Released exactly once; escrow locked goes to zero; exporter credited; ledger conserved; audit complete. |
| TC-002 | Same fixture but bill-of-lading shipment reference or invoice amount mismatched. | Created → Pending → Under Review; payout blocked; mismatch fields shown; manual revalidation required; no silent overwrite. |
| TC-003 | Same fixture with simulated AML ALERT before release. | Created/Pending → Frozen; no payout; restricted read-only alert evidence; authorised compliance resolution required. |

### Expanded regression matrix — minimum recommended

| ID | Condition | Expected safety/result |
|---|---|---|
| TC-004 | Insufficient funds at creation | Create rejected; balances unchanged. |
| TC-005 | Creation KYC FAIL | No active funded escrow. |
| TC-006 | No shipment attestation | Cannot enter releasable state. |
| TC-007 | Shipping attestation for another trade | Rejected as cross-trade evidence. |
| TC-008 | Missing customs/document field | DOCUMENTS not PASS; remain pending/review. |
| TC-009 | Corrected document with new revision | Old approval invalidated, new review needed. |
| TC-010 | Expired KYC clearance at release | Freeze/block, require new compliance decision. |
| TC-011 | AML alert after previously passing checks | Freeze overrides older PASS. |
| TC-012 | Release pressed twice | One transfer only; second operation safely rejected/idempotent. |
| TC-013 | Refund pressed twice | One refund only. |
| TC-014 | Refund attempted during unresolved AML hold | Blocked pending authorised resolution. |
| TC-015 | Exporter attempts to approve compliance | Access denied and event captured. |
| TC-016 | Regulator attempts state-changing action | Access denied; read-only audit remains available. |
| TC-017 | Importer tries another trade's documents | No cross-trade data access. |
| TC-018 | Ledger entry edited after logging | Validation script detects tampering if hash-chain is claimed. |
| TC-019 | Force race/concurrent release commands | Supply conserved; single terminal outcome. |
| TC-020 | Ambiguous/equally timed evidence revisions | Deterministic priority/version resolution documented. |
| TC-021 | Review corrected and cleared | Under Review → Pending → Released only after fresh release gates. |
| TC-022 | Unresolved non-AML mismatch terminates | Documented authorised refund/termination with audit entries. |
| TC-023 | Fresh AML clearance after authorised review | Frozen → Pending/Under Review; not direct unconditional release. |
| TC-024 | Export/download audit with restricted fields | Only permitted fields displayed/exported for each role. |

**Tests must include negative controls.** Passing TC-001–003 does not prove robust exception handling, concurrency safety or privacy. Prefer test counts with transparent denominator (e.g. `22 / 24 passed`) rather than invented “100% accuracy”. All test success values and timing statistics must be generated by actual runs; **the above rows are specifications, not results**.

## II.7 Evaluation design and reproducible metrics

### Measurement table

| Metric | Operational definition | Evidence and interpretation |
|---|---|---|
| End-to-end simulated settlement time | Simulation-clock elapsed time from **declared common start event** to payment completion, separately recording pre-funding and exception durations | Explain assumptions in baseline and escrow; show median, range and scenario class. |
| Post-shipment release latency | Time from verified shipment + all documents available to recipient payment confirmation | Isolate automated release benefit; distinguish from full transaction time. |
| Manual effort | Count of distinct human-performed tasks / approvals per completed case | Derive from BPMN and event taxonomy; not from arbitrary UI clicks. |
| Total process steps | Number of defined process tasks/gateways under consistent inclusion rules | Publish both process maps and counted task list. |
| State-transition execution accuracy | `number of correct transition/outcome assertions ÷ total assertions tested` | Automated test report, with denominator and failure IDs. |
| Release/exception safety | `unauthorised release attempts correctly blocked ÷ total negative release attempts` | Compliance/control tests, not customer fraud detection accuracy. |
| Audit completeness | `mandatory lifecycle events present with required fields ÷ total expected lifecycle events` | Audit checker output; include denied operations. |
| Role-limited visibility | `% of role-policy test cases obeyed`; inspect regulator vs commercial visibility | RBAC tests + screenshots/export fixtures. |
| Funding lock-up (trade-off) | Time × locked amount, e.g. HKD-days for synthetic example | Compare only under clearly stated baseline; do not claim economic gains without finance cost assumptions. |
| Peer usability/clarity | Descriptive 1–5 survey distribution for 8–10 planned peers (if actually obtained) | Report n, questions, averages/medians and response limitations. |

### Correct comparator design

1. Fix the **same trade value, parties, shipping milestone, documentary requirements and two compliance checkpoints** where comparable. Record if the open-account baseline materially differs in legal/economic structure.
2. Specify baseline step and duration assumptions **before looking at results**. Prefer assumptions from documents or clearly labelled expert estimates. If none, run transparent scenarios (e.g. low/base/high manual-review duration) instead of claiming an observed real-world time-saving.
3. Record separate `t_order`, `t_escrow_funded`, `t_shipment`, `t_documents_ready`, `t_release/receipt`. Do not mix “post-shipment latency” with “entire payment cycle”.
4. Use an explicitly defined clock: **logical/simulated durations** for business steps; **wall-clock computation duration** for engine runtime. These two must never be presented as the same measure.
5. Run reproducible baseline and proposed workflows with identical fixture IDs, fixed random seeds (if any), configuration, hardware environment and code revision. Provide a command to reproduce tables.
6. Report **neutral or adverse findings** as valid findings. For example, escrow may reduce handoffs but introduce earlier funding and more reconciliation steps.
7. Do not use generic published 7–15-day documentary-credit processing estimates as an open-account comparator; a letter of credit is a different product. Likewise, do not treat a 24/7 HKMA pilot as empirical evidence that this student app has real-time settlement.

### Formulae to compute from actual outputs

```text
Manual-step reduction (%) = 100 × (M_baseline − M_escrow) / M_baseline
Post-shipment latency reduction (%) = 100 × (L_baseline − L_escrow) / L_baseline
Transition accuracy (%) = 100 × Correct assertions / Total assertions
Audit completeness (%) = 100 × Required event records present / Expected required event records
```

If denominator is zero, show `not defined`, not zero or infinity. Aggregate by scenario, not across incompatible cases without explanation. Chart axes must start meaningfully, show units and disclose sample counts. Do not report uncertainty estimates from only three hand-picked case demonstrations.

## II.8 Scenario evidence protocol: collect data once, reuse in all deliverables

**Every experiment should produce an immutable evidence bundle** (relative paths are recommendations):

```text
results/
  run_manifest.json               # timestamp, commit SHA, seed, app version, rule config
  scenarios_summary.csv           # one row / test, expected vs actual, pass/fail
  metrics.csv                     # raw counts and times with units / definitions
  baseline_assumptions.csv        # manual workflow assumptions, sources, rationale
  events/TC-001.jsonl
  events/TC-002.jsonl
  events/TC-003.jsonl
  screenshots/TC-001-creation.png
  screenshots/TC-001-release.png
  screenshots/TC-002-review.png
  screenshots/TC-003-freeze.png
  audit_access_matrix.csv
  survey_anonymised.csv           # only if peers participated
  evidence_index.csv              # claim → test/run/file/figure/citation
```

**Claim taxonomy for every output:**

- `OFFICIAL_FACT`: directly supported by an HKMA/ADB/BIS/ISO/other authoritative document with date and URL.
- `SIMULATION_RESULT`: produced by this team's execution and linked to source code, fixture, timestamp and export.
- `ASSUMPTION`: scenario or comparator parameter, explicitly labelled and justified.
- `EXPECTED`: forecast/design intention, **not** measured.
- `LIMITATION`: unimplemented / conceptual / outside scope.

**Example of an allowable final claim:** “Under the predefined, synthetic process assumptions, the prototype reduced manual approval steps from **[observed baseline]** to **[observed proposed]** in case TC-001. This does not establish actual production time or cost savings.” Replace placeholders only from measured exports.

## II.9 Peer evaluation and feedback (proposal-consistent)

**[BASELINE]** Target roughly **8–10 peers**, with 5-point Likert items on usability, process clarity and logical consistency, plus an optional open comment. [P1]

**Suggested questionnaire:**

1. “The transaction status was easy to understand.” (1 strongly disagree … 5 strongly agree)
2. “The steps required to release funds were clear.”
3. “I could understand why the system blocked a document mismatch.”
4. “I could understand why an AML alert froze funds.”
5. “The difference between a simulation and a real financial system was clearly communicated.”
6. “Which step was most confusing?” (open response)
7. “What one design change would be most useful?” (open response)

Provide same task script to each volunteer. Get voluntary participation; do not gather confidential data. Record number invited/responded, experience level if volunteered, questionnaire date, and count of valid responses per item. An n=8 sample supports **formative feedback**, not statistical generalisation to bankers or users. Never fabricate participants, expert interviews, sample sizes or a survey result.

## II.10 Conceptual e-HKD extension: precise and bounded

**[BASELINE]** Present a two-leg concept: simulated tokenised commercial-bank deposit leg and e-HKD/central-bank-money leg, both complete or neither completes. [P1]

**Suggested illustration:** `PREPARE both legs → validate mock balances/permissions → COMMIT both in one toy transaction → display finality of BOTH or rollback BOTH`. Inject failure in leg B and demonstrate rollback in both simulated balances. Declare that actual multi-ledger atomicity, legal settlement finality, central bank operation, real interoperability and FX are **not implemented**. 

**Current public context (do not retroactively change the submitted 25 Sep proposal):** HKMA announced on **2 Nov 2026** that EnsembleTX supports **24/7 interbank settlement of tokenised deposit transactions in tokenised central-bank money**, with **12 participating banks and 20 industry pioneers** [R1]. This is a genuine development since the proposal was submitted; discuss in the final report's “Recent developments” subsection as new context, not as the team's own accomplishment or as proof of compatibility. Project mBridge reached MVP in mid-2024 and is described by BIS as a distinct multi-CBDC project; do not say this student prototype runs on mBridge [R4].

## II.11 Security, legal, regulatory and research integrity

- Mock KYC/AML pass/fail flags are **simulation inputs**, not confirmation that actual Hong Kong or Thai statutory requirements have been met. HKMA's AML/CFT supervisory material and applicable legal obligations must be cited in the final discussion [R6].
- Audit access is **read-only and least-privilege** by default. Access to commercial document bodies should require separately modelled authorisation. Treat regulator permission as a scoped representation, not universal access to raw data.
- Make user-role switching obviously a **demo control**; it is not a real identity-verification mechanism. Enforce RBAC in service methods and tests nonetheless.
- Do not store secret keys in source code; do not access live banking APIs or collect IDs and bank account details. If any external deployment is used, protect it, serve synthetic fixtures only and avoid public writes to production-like databases.
- Handle invalid form inputs, duplicated operations, stale documents, failed checks, concurrent actions and restart persistence; preserve an accurate audit event for denied attempts.
- Separate *record immutability in the teaching demo* from legal enforceability and real distributed resilience. NIST SSDF provides optional software quality and security practice guidance [R9].
- Trade document comparisons should be field-based and realistic, but do **not** equate your open-account workflow with UCP 600 documentary credit processing. UCP 600 [R10] can provide context for documentary requirements **only if the paper distinguishes these products**.
- If implementing ISO 20022-like messages, explicitly say **“ISO 20022-inspired mock fields”** unless the application produces schema-valid messages against a specified version; the ISO catalogue [R7] is authoritative for format/version selection.

## II.12 External facts and data worth using (verified public sources)

The original proposal's historical statements are preserved as the submission baseline. The final work may use newer public context **with dates**, cited independently. The table below lists facts suitable for an evidence-backed background slide or report. Do not confuse **public facts** with **simulation output**.

| Verified fact and correct qualifier | Reputable source | Where it belongs |
|---|---|---|
| Hong Kong was Thailand's 13th-largest trading partner in **2023**, total bilateral trade **US$13.7bn** (historical figure). | EXIM Thailand, 23 Feb 2024 [R5] | Problem/corridor context; label 2023. |
| ADB reported global trade finance gap **US$1.7tn in 2020** and SMEs were **40% of rejected trade finance requests** in that survey. | ADB, 12 Oct 2021 [R3] | Explain historical proposal source; not current figure. |
| ADB's more recent survey estimates gap **US$2.5tn in 2025** (its Jan 2026 release); **approximately 10% of global trade**. | ADB, 15 Jan 2026 [R2] | Updated final-report context; do not mix 2020 and 2025. |
| HKMA Project CargoX report estimates **HK$311.2bn–HK$519.1bn** Hong Kong 2024 trade-finance gap; this is **not** an SME-only figure. | HKMA Project CargoX recommendation report [R11] | Local-scale context; use estimate range. |
| HKMA launched CargoX Pilot Programme in **May 2026**, involving **21 banks**, to advance cargo/trade data cases. | HKMA, 7 May 2026 [R12] | Contrast data interoperability/verification with escrow scope. |
| HKMA EnsembleTX launched in **Nov 2025**; by **2 Nov 2026** it supported **24/7 tokenised CeBM interbank settlement**, with 12 banks/20 industry pioneers. | HKMA, 2 Nov 2026 [R1] | Recent context; explicitly not the student app. |
| e-HKD Phase 2 studied tokenised-asset settlement, programmability and offline payments; HKMA prioritised institutional wholesale development after pilots. | HKMA e-HKD Phase 2 Report, Oct 2025 [R13] | Distinguish e-HKD from commercial bank deposits. |
| mBridge achieved **MVP mid-2024**, distinct from Project Ensemble and this prototype. | BIS Project mBridge [R4] | Cross-border infrastructure comparison. |

**Avoid false inference:** ADB financing gaps are **unmet finance demand**, not a forecast of savings from escrow. HKMA CargoX digitises cargo/trade data; it is not an implementation or endorsement of this team's solution. The existence of tokenised CeBM infrastructure does not establish legal permission for this exact simulated escrow.

## II.13 Complete Part II deliverables, acceptance and stop rules

The executing models should deliver the following exact artefact classes; paths may differ if documented in a manifest:

| Deliverable | Minimum quality / definition of done |
|---|---|
| `README.md` and `requirements.txt`/lockfile | One command to install/run; Python version and all dependencies pinned; clean environment replay verified. |
| `app/` and documented architecture | Functional Streamlit demo and backend engine with persistent mock state; no inert buttons represented as features. |
| `domain_model.md` + schema files | Money model, states, actors, ownership, claim limits and field types consistent. |
| `diagrams/baseline.bpmn` and `proposed.bpmn` | Correct BPMN gateways, swimlanes and two comparable processes. |
| `diagrams/state_machine.svg` and `architecture.svg` | Same six states, trust boundaries, data flow, authorisation and money movement. |
| `fixtures/*.json` or `.csv` | Synthetic, deterministic, validated data; normal and negative cases. |
| `tests/` + `pytest` output | Core cases plus expanded edge tests run against service layer; pass/fail report, no fabricated rates. |
| `results/` evidence bundle | Raw event logs, comparable metrics and screenshot index linked to test IDs. |
| `evaluation_method.md` | Metric equations, clocks, comparator assumptions, uncertainties, trade-offs, denominators. |
| `peer_feedback.md` + anonymised data (if obtained) | Actual responses and methods, or explicitly “not collected”. |
| `eHKD_extension.md` and small optional demo | Illustrative atomic operation with rollback and scope warning, no real CeBM claim. |
| `limitations_and_risks.md` | Real deployment limitations: issuer liability, legal ownership, finality, compliance review, dispute/fraud, custody, interoperability, data access, liquidity. |

**Release gate:** No “final complete” status until app runs on clean setup, three flagship demos execute, test exports are reproducible, control invariants are verified, the baseline is fair and documented, and every reported number has an evidence ID. “UI done” is not synonymous with “project done”.

---

# PART III — FINAL PROJECT REPORT (20% OF COURSE)

## III.1 Official constraints and substantive target

**[COURSE]** Due **19 November 2026, 23:59**, **20%** of course grade, with the **15-page limit excluding cover, contents, executive summary, appendices, figures and references**, and **individual self-reflections**. Requirements include problem analysis, weaknesses of early implementations, innovative elements, system design, experimentation and outcome evaluation. The instructions do not prescribe a specific citation style, font, exact table count or minimum statistical sample. Do not invent these as course requirements. [C1]

**Editorial goal:** Treat it as a **completed technical study**, not a rewritten proposal. Replace future-tense promises with implemented methods and measured results only where verified. Be candid when planned components were not implemented or claimed improvements did not materialise. Retain the formal project name and commitment boundaries from [P1].

## III.2 Recommended report architecture and page budget

The team should aim for **~12–14 counted body pages**, leaving a buffer below the official cap. Suggested proportions are authoring guidance, not rules imposed by CUHK:

| Body section | Target body pages | Mandatory content / core exhibit |
|---|---:|---|
| 1. Problem Definition and Current Financial Infrastructure | 1.5 | Corridor, pain points, open-account process, risk and sources [R2,R5,R11,R12]. |
| 2. Existing Initiatives and Gap Analysis | 1.5 | Project Ensemble/EnsembleTX, e-HKD and mBridge: what each addresses, what remains unsolved; distinguish 2025 vs 2026 [R1,R4,R13]. |
| 3. Research Question, Scope and Assumptions | 0.75 | Hypotheses, realistic exclusions, pre-funding trade-off, synthetic and non-live status. |
| 4. Architecture and Innovation | 2.0 | Trust diagram, seven roles, off-chain verification, token ledger, privacy and control decisions. |
| 5. Smart-Contract Escrow and Exception Logic | 2.0 | Six-state diagram, release guard, mismatch/AML resolution, invariants and permission matrix. |
| 6. Experimentation Methodology | 1.5 | Baseline-vs-proposed design, fixtures, 3 main + edge cases, clock and metrics. |
| 7. Results and Evaluation | 2.0 | Reproducible tables/charts, pass/fail, manual steps, latency, audit access, qualitative feedback if collected. |
| 8. Discussion, Limitations and Feasibility | 1.0 | Improvements **and** pre-funding/law/FX/interoperability/legal finality/AML limitations. |
| 9. Conclusion and Future Work | 0.5 | Answer central question with appropriate limits; future e-HKD integration not a delivered product. |
| **Indicative counted total** | **12.75** | Include concise cross-references to appendix and figures. |

**Outside counted body, as specified by course:** cover, TOC, executive summary, appendices, figures and references. Follow course interpretation of “figures” rather than moving ordinary narrative into figures to manipulate page count. Include **one individually attributed, substantive self-reflection for each member**, in an appropriately designated section/appendix consistent with instructor expectations. The submission/VeriGuide declaration requires every member's agreement/signature as applicable [C1].

### Exact analytical content of key sections

**Section 2 — Do not merely list HKMA programmes.** Use a matrix: `initiative`, `money/infrastructure type`, `real demonstrated capability`, `what it does NOT solve for our case`, `relationship to mock escrow`, `source/date`. A recent-policy-update paragraph should cite HKMA **2 Nov 2026** CeBM upgrade [R1]. Do not claim the official proposal predicted this milestone.

**Section 4 — Make the architecture falsifiable.** Explain why a mock ledger is used, where shipment/document/compliance information enters, what may be forged or stale, what data must remain private, how bank and regulator views differ and how trade-money claims are accounted for. State why off-chain attestations are necessary. Include trade-off versus an ordinary database and avoid asserting “DLT is always superior”.

**Section 5 — Prove the engine works.** Provide representative rule logic, state transitions, balance invariant, dual KYC/AML checkpoints, role permissions and review/freeze policy. Show at least one adverse/failed scenario evidence chain, not just a normal flow.

**Section 6 — Make comparisons fair.** Describe baseline flow, pre-funding, fixture, assumptions and metrics explicitly. If latency values are simulated, title the chart “Modelled workflow duration under stated assumptions”, not “real transaction speed”. Explain number of tests, case selection and qualitative review method.

**Section 7 — Results must be actual outputs.** Table of all flagship and selected negative tests, expected/actual result, numerator/denominator, sample/time distributions, manual steps, post-shipment latency, and one audit screenshot or event extract; discuss adverse results and any failures. If the project has not gathered 8–10 peer responses, do not invent them; write “feedback pending/unavailable” and adjust limitations.

**Section 8 — Strong critical discussion:** identify cost/benefit and who bears it. Pre-funded escrow shifts liquidity burden to importer; off-chain sources are trust bottlenecks; document correctness does not prove physical goods quality; mock “compliance” is not regulatory authorisation; single-bank synthetic claims cannot prove cross-border legal finality; dispute resolution and legal rights require governance. No live cross-border or real atomic settlement claim.

## III.3 Visuals and empirical figures: what to create and what not to create

Recommended defensible figures:

1. **Swimlane BPMN pair** — baseline and proposed process; reference shared step IDs.
2. **Architecture and trust-boundary diagram** — separate off-chain modules, escrow state engine, ledger and seven participant views.
3. **Six-state transition graph** — labeled release guards and exception routes.
4. **Actual scenario assertion table** — true `n passed / n run` from test runner.
5. **Manual task counts by process** — compare only equivalent tasks; visible integer axis and denominators.
6. **Two latency plots** — post-shipment versus full cycle with clear simulated assumptions and funding milestone.
7. **Audit-event sequence extract** — event IDs/actors/timestamps/reason codes; redact fixture contents if appropriate.
8. **Peer feedback distribution** — only if actual respondents participated; avoid false precision from n≈8–10.

**Prohibited presentation practices:** invented “industry” benchmark bars; unlabeled mock data; “100% security” claims; stock charts with fictitious 12,000+ transactions; numbers that don't match raw CSV; real-world throughput claims based on Streamlit UI click timings; and citations that do not support the exact claim.

## III.4 Required interpretation and source quality

Use **primary sources** before secondary summaries. Trace every factual number to a date, institution, URL and source excerpt. Suggested reference group: HKMA policy/cargo data [R1,R11,R12,R13], BIS mBridge [R4], ADB trade-finance surveys [R2,R3], EXIM Thailand bilateral data [R5], HKMA AML [R6], ISO 20022 [R7], OMG BPMN [R8], NIST security [R9]. Consider UCP 600 [R10] only as contextual documentary-credit material with correct product distinctions. Cite specific software libraries separately if their functions underpin design decisions.

**Use research responsibly:** Recent external programme milestones may differ from old proposal wording. Say “At the time of proposal submission...” versus “As of 2 Nov 2026...”. Report both without overwriting the official submitted original.

**Evidence-to-claim checklist:** before each figure/table or asserted result, verify (i) scenario ID; (ii) run date and build hash; (iii) data provenance; (iv) numerator and denominator; (v) units, period and compared segment; (vi) uncertainty/assumption; (vii) correct citation or test artifact.

## III.5 Personal self-reflection: individual and evidence-based

Each of four members should write **their own** reflection (not model-invented): assigned work and actual contribution; one problem and how it was resolved; one limitation or feedback response; lessons about infrastructure risk, teamwork, system design and trade-offs; what they would change. If responsibility assignments are not yet available, request them from each member rather than making them up. AI may assist editing only with truthful acknowledgement. Do not attribute technical implementation to a specific member unless substantiated.

## III.6 Report production and review workflow

1. Freeze Part II source code, fixtures, results manifest and evaluation assumptions.
2. Create a **claim–evidence ledger** (a table mapping each quantitative/technical claim to test export or official source).
3. Generate tables/charts **from raw results**, not manually redrawn data; reconcile numbers.
4. Draft Sections 4–7 **first** around evidence, then Sections 1–3 and 8–9; finally write executive summary.
5. Format figures for print/readability, consistent citations and glossary; ensure body limit.
6. Obtain four actual individual reflections and correct course AI acknowledgement, academic honesty declaration and reference list.
7. Conduct technical peer review, fact check, language/grammar review, rendered-page and PDF export review. Verify no orphan figure, broken reference or missing appendices.
8. Submit by official 19 Nov deadline; keep the submission receipt and exact final file hash. Never rely on a local file's modification time as proof of submission.

**Final report package:** `FTEC3002_Group1_Final_Report.docx` (or required upload format), verified PDF preview, `references.bib`/reference list, `evidence_index.csv`, diagrams and appendices, `submission_checklist.md`, and separately retained source/CSV logs. Check Blackboard for format instructions not stated in the course outline.

---

# PART IV — FINAL PRESENTATION SLIDES (15% PRESENTATION COMPONENT)

## IV.1 Purpose, constraints and relation to report

**[COURSE]** Slides due **22 November 2026, 23:59**; presentations on **24 November / 1 December 2026**; presentation assessment weight **15%**. The outline says the presentation should introduce **innovative elements, pilot experiments and achieved outcomes**. It does not prescribe the number of slides or speaking minutes; obtain these from instructor/Blackboard and scale the recommended deck accordingly. [C1]

**Editorial rule:** The deck should be a **high-quality visual explanation of actual completed research**, not a projection of an imaginary bank-grade product. It may have an advanced visual style developed by another model, but evidence is always more important than decoration.

## IV.2 Recommended final presentation sequence (12 main slides; optional backup)

| # | Slide argument (a conclusion, not just a topic) | Evidence/visual expected |
|---|---|---|
| 1 | **HK–TH TradeEscrow: condition-based release with visible controls** | Strong project title, team, one real prototype image or architecture fragment. |
| 2 | **The problem is fragmented verification and settlement decision-making** | Hong Kong–Thailand corridor and 2–3 accurately dated pain-point figures [R2,R5,R11]. |
| 3 | **Our research hypothesis is narrower than a live cross-border CBDC** | Research question, low-fidelity scope and measurable success criteria. |
| 4 | **We replace manual handoffs with rule-driven escrow gates** | Side-by-side baseline vs proposed BPMN, funding milestone highlighted. |
| 5 | **The product works through seven roles and off-chain attestations** | Architecture and roles; explicit mock vs live boundaries. |
| 6 | **Release is impossible until three independent gates pass** | Six-state diagram + actual guard explanation, no magic smart-contract data access. |
| 7 | **A normal synthetic trade completes with an auditable release** | Live app/screenshots of TC-001 and balance/event evidence. |
| 8 | **Bad documents and AML alerts stop the transaction safely** | TC-002 and TC-003 state traces and denied-release evidence. |
| 9 | **The test suite covers both success and failures** | True test matrix counts, negative tests, pass/fail, error investigation. |
| 10 | **The evaluation shows what changed — and what did not** | Measured manual steps, comparable simulated latency, trade-offs and assumptions. |
| 11 | **Policy alignment is real; e-HKD interoperability is conceptual** | HKMA 2026 EnsembleTX milestone and separate illustrative atomic leg [R1]; sharp limitation notice. |
| 12 | **Conclusion: a useful demonstrator, not a production settlement system** | Exact evidence-backed takeaways, limitations, future steps. |

**Optional backups:** role-permission matrix, release rule pseudocode, detailed test cases, funding lock-up assumptions, survey methodology/results, reference links and business process definitions. Put full citations in speaker notes/end references and short `[n]` labels on visual claims.

### Demo placement and fallback

If live demos are allowed and dependable, schedule **one controlled demo around slides 7–8**; otherwise use a pre-recorded clip captured from the final verified build. Keep `TC-001`, `TC-002`, `TC-003` loaded locally with a reset function. The presenter must be able to show **both** a release and a blocked release without revealing real data. Have static screenshots if the app or network fails.

**Non-negotiable presenter script points:** (a) pre-funded vs open account; (b) three off-chain gates; (c) six states; (d) role-specific audit; (e) simulation only; (f) what was actually measured; (g) why off-chain trust, liquidity lock-up and law remain unresolved.

## IV.3 Charts and visuals — integrity rules for visual execution models

A strong design model can choose visuals, typography and colour independently. Nevertheless:

- Use **real screenshot assets captured from the team's app**; label conceptual mockups as conceptual.
- Chart data **must come from** `results/metrics.csv`, `scenarios_summary.csv` or anonymised survey data. Cite exact file/run in slide notes.
- For public background data, **never blend time periods**: e.g. 2020 ADB US$1.7tn vs 2025 ADB US$2.5tn; 2024 HKMA HK$311.2bn–519.1bn; label currencies and years.
- Prefer two-process swimlane, state-transition graph, evidence matrix, latency decomposition and pre-funding trade-off over decorative dashboards with fictional bank telemetry.
- Maintain large readable type, colour contrast, sensible chart axes/units, no tiny footnotes as the sole place conveying limitations.
- Distinguish `Simulated`, `Observed in prototype`, `Assumed`, `Official external statistic`, and `Conceptual extension` consistently in captions.
- No fabricated approval, official logo endorsement, bank deployment screenshots, or customer counts.
- If a source figure is recreated, cite it, preserve its meaning and avoid misrepresenting the original source.

## IV.4 Presentation delivery, role allocation and Q&A

**Team roles must be assigned after checking actual contributions**; the proposal only identifies the four team members, not who is backend/frontend/analysis/presenter. A possible function-based handoff plan is: (i) domain/research, (ii) core engine/data, (iii) experiment/evaluation, (iv) writing/design and QA — with cross-review from all. Do **not** represent these as assignments already agreed by the team.

Prepare concise responses to these likely expert questions:

| Question | Evidence-backed response expected |
|---|---|
| Why use DLT rather than a normal database? | Permissioned shared audit/provenance **concept**; honest admission that our prototype uses a mock ledger and cannot prove DLT superiority without a network/governance deployment. |
| How can a contract know goods shipped? | It cannot directly; a trusted/off-chain logistics attestation is supplied, is versioned and may be wrong or forged. |
| Is this compliant with HK or Thai AML laws? | No formal compliance claim; synthetic attestations demonstrate where controls belong, not legal certification. |
| What happens when there is an AML alert or document dispute? | State freeze/review with funds locked, actor authorisation, evidence and explicit resolution, no auto release. |
| Are tokenised deposits, stablecoins and e-HKD the same? | No; different issuers, claims, risks and regimes. Extension is a separate conceptual two-leg illustration. |
| Did it settle real cross-border funds / use mBridge or EnsembleTX? | No; precisely no bank or central-bank connectivity, no real FX or legal finality. |
| Does your system make settlement faster? | Only what the **defined simulation** shows; separately discuss full-cycle funding and liquidity burden and baseline assumptions. |
| What happens if the oracle or document checker lies? | It is a residual trust risk; review, signed source, expiry, evidence and governance are needed; app does not solve physical-world truth. |
| Is the system auditable without exposing all private commercial data? | Role-limited event metadata and authenticated access; role-policy tests; qualified privacy/security claim. |
| What changed after the proposal was submitted? | HKMA's 2 Nov 2026 EnsembleTX 24/7 CeBM upgrade; source and date, separate from our own demonstration. |

## IV.5 Final slide QA and delivery package

**Pre-flight:** All 12 arguments map to a precise section or dataset in the final report; counts/units agree; presentation can be delivered by whichever members are actually available; there is no uncited numerical headline; demo functions offline/on fallback; every URL/citation works; rendered PDF pages have no clipping/overlap; slide animation cannot hide core evidence; optional speaker notes contain the detailed methodology and references.

**Expected outputs:** editable `HKTH_TradeEscrow_Final_Presentation.pptx`, matching preview PDF, speaker notes/script (separate or inside PPTX), `slides_evidence_map.csv`, demo media/backup screenshots, Q&A brief and a timed rehearsal record. Actual visual/execution models own the artwork and slide engineering; they are **not authorised to change outcomes or fabricate metrics**.

---

# COORDINATION RULES FOR ALL EXECUTION MODELS

## Model/workstream division — assign by responsibilities, not imaginary member names

| Workstream owner type | Receives | Must deliver | Review by |
|---|---|---|---|
| Product / financial infrastructure research model | Official proposal, course outline, public references | Verified research memo, claims register, baseline assumptions, privacy/legal limitations | Independent fact-check model |
| Domain/state-engine implementation model | Part II schema, transition matrix, rules and fixtures | State engine, token postings, tests, CLI replay, logs | Security/testing model |
| App/UI engineering model | Service contract, role matrix, fixture commands | Streamlit app, real interactions and demo mode | Engine owner + QA |
| Experiment/statistics model | Test runner and baseline assumptions | Reproducible study and results; honest charts and limits | Independent numerical QA |
| Interim presentation model | Dated tested build, progress score, actual captures | Short interim deck and proof-backed talk track | Progress/data reviewer |
| Report-writing model | Verified research and final experimental evidence | Final report and separate member reflection requests | Technical+source reviewer |
| Final slide design model | Final report, evidence map, demo captures | Editable deck, PDFs, speaker notes | Fact and visual QA |
| Project integrator (one designated team member) | All workstreams | Consistent final deliverables, versioning, schedule, submission receipt | Entire team |

**Handoff contract:** Every model must (1) state exact files read, (2) preserve baseline scope, (3) list changed/new files, (4) give a reproducible way to check deliverables, (5) distinguish actual results from expected results, (6) give source URLs and dates, (7) note unresolved risks, and (8) not claim that code/tests/UI are complete without corresponding artefacts. The coordinator keeps a single requirements-and-evidence matrix.

## One canonical project directory (recommended)

```text
HKTH-TradeEscrow/
├── official_inputs/             # submitted proposal and course outline (read-only)
├── research/                    # references, claims, source excerpts, gap analysis
├── requirements/                # traceability, assumptions, role policy, risk register
├── diagrams/                    # BPMN, architecture, state machine, money flows
├── app/                         # Streamlit UI, domain service, persistence, mock modules
├── fixtures/                    # synthetic trade and attestation data
├── tests/                       # tests for success, exceptions and permissions
├── results/                     # verified immutable run manifests, CSV and event logs
├── interim/                     # dated update PPTX/PDF and progress evidence
├── report/                      # final paper, figures, references and member reflections
├── presentation/                # final PPTX, PDF, script and Q&A
├── docs/                        # README, user guide, limitations, method notes
└── guidance.md                  # this file
```

**Branch/review rule:** No model may silently change `official_inputs/`. Integrate through reviewed pull requests/patches or an explicit file change log. Lock a results version before writing the final report. If findings change, regenerate all downstream tables/charts/slides from the new run and note the revision.

## Critical path (starting 7 Nov 2026; internal planning, not a course directive)

| Target | Action | Gate |
|---|---|---|
| **By 9 Nov update** | Freeze scope + BPMN + working escrow engine + primary scenario smoke tests + interim evidence and deck | Honest 70–80% target **only if demonstrated**. |
| **10–12 Nov** | Finish regression suite, role/ledger QA, exception controls, robust fixture replay | All major tests executable; unknown issues logged. |
| **12–14 Nov** | Run controlled comparator, capture metrics, peer questionnaire (if feasible), e-HKD conceptual demo | Dated manifest and raw evidence available. |
| **14–16 Nov** | Lock working prototype and results; draft report around verified findings, figures and limitations | Independent review of source and numerical claims. |
| **17–18 Nov** | Complete four authentic reflections, format report, check 15-page limit and AI disclosure/declaration | Final report submission-ready. |
| **19 Nov** | Submit report before 23:59 | Verify receipt; preserve submitted artefact hash. |
| **20–21 Nov** | Finish final deck from frozen result set, record fallback demo and rehearse | Evidence and report/slides consistency check passed. |
| **22 Nov** | Submit slides before 23:59 | Preserve receipt and PPTX/PDF fidelity. |
| **24 Nov / 1 Dec** | Deliver presentation on assigned date | Presenter and demo readiness; answer examiner questions candidly. |

**Most time-sensitive risk:** The report due **19 Nov** precedes the slide deadline. Prioritise **working evidence and report readiness** over speculative UI extras, AI chatbots, live integrations or fancy marketing graphics.

## Definition of success and failure for this project

**Minimum credible finished project:** A team can start a clean app, replay TC-001/002/003, inspect six-state transitions, see funds locked/released/refunded only under guard rules, test role-limited audit visibility, compare a transparent manual baseline, reproduce metrics, discuss why results cannot be generalised to actual trade finance and demonstrate a conceptual e-HKD extension (if implemented) labelled honestly.

**What would invalidate the work:** A front-end-only mock represented as a working settlement engine; generated statistics with no tests; fake survey respondents; treating AML mock flags as real clearance; releasing funds under unresolved compliance hold; reporting real cross-border payments or e-HKD use without them; replacing the official proposal with an old draft; or a report whose numbers disagree with slides.

## Questions that the team must resolve internally (do not block the initial work)

- What is the exact assigned presentation date and talk duration? Verify Blackboard/instructor.
- Which members actually own code, research, evaluation, final writing and presentation? Record assignments but do not invent them.
- Does the instructor prefer DOCX/PDF, separate declaration or specific submission route? Confirm in current Blackboard instructions; the course outline alone does not answer every format detail.
- Is a protected public demo URL feasible and allowed, or should demonstration be local/offline? Either is acceptable within the simulated scope.
- Which baseline manual step durations can be justified with sources? Use explicit scenario assumptions if actual empirical process data are unavailable.
- Will peers participate voluntarily before the report deadline? If not, report this as a study limitation.

---

# REFERENCE AND FACT-CHECK REGISTER

## Primary team documents (provided by user)

- **[P1]** `FTEC3002_Group_1_Project_Proposal.docx`, Group 1, officially submitted project proposal dated 25 September 2026. **Only approved project baseline** for this guidance. Its Sections 1–9 define requirements; reference list and AI acknowledgement remain part of the submission.
- **[C1]** `FTEC3002 Course Outline (2026-27) v1.2(1).pdf`, CUHK FTEC3002, pp. 3–8: teaching schedule, assessments (p.4), project development flow (p.5), grading/report criteria (p.6), academic integrity and AI rules (pp.7–8). This is the source of course requirements.
- **[EX1]** `Group 6(update) (1).pptx`, 17 slides. **Reference example only**, not evidence, benchmark, or source of technical requirements for Group 1.

## Independently checked public sources (as of 7 Nov 2026)

- **[R1] HKMA (2 Nov 2026).** “HKMA advances Project Ensemble pilot phase to 24/7 settlement in tokenised Central Bank Money.” https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/11/20261102-5 — official dated current development and 12 banks / 20 industry pioneers.
- **[R2] ADB (15 Jan 2026).** “Demand for Trade Finance to Rise Amid Supply Chain Realignment—ADB Report.” https://www.adb.org/news/demand-trade-finance-rise-amid-supply-chain-realignment-adb-report — 2025 global gap US$2.5 trillion, about 10% of global trade.
- **[R3] ADB (12 Oct 2021).** “Global Trade Finance Gap Widened to $1.7 Trillion in 2020.” https://www.adb.org/news/global-trade-finance-gap-widened-17-trillion-2020 — historical 2020 gap and share of rejected requests involving SMEs.
- **[R4] BIS.** “Project mBridge.” https://www.bis.org/project/mbridge — official project profile; MVP mid-2024 and programme scope.
- **[R5] EXIM Thailand (23 Feb 2024).** “EXIM Thailand Inks MOU with Hong Kong Trade Development Council to Foster Thailand–Hong Kong Trade and Investment.” https://www.exim.go.th/EN/Newsroom/newsactivities/EXIM-BANK-%E0%B8%A5%E0%B8%87%E0%B8%99%E0%B8%B2%E0%B8%A1-MOU-%E0%B8%81%E0%B8%9A%E0%B8%AD%E0%B8%87%E0%B8%84%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%AA%E0%B8%A0%E0%B8%B2%E0%B8%9E%E0%B8%92%E0%B8%99%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%84%E0%B8%B2%E0%B8%AE%E0%B8%AD%E0%B8%87%E0%B8%81%E0%B8%87-%E0%B8%AA%E0%B8%99%E0%B8%9A%E0%B8%AA.aspx — 2023 bilateral trade and rank. Thai-language URL segment is reproduced from the verified EXIM result; test hyperlinks after copying into a report.
- **[R6] HKMA.** “Anti-Money Laundering and Counter-Financing of Terrorism.” https://www.hkma.gov.hk/eng/key-functions/banking/anti-money-laundering-and-counter-financing-of-terrorism/ — official AIs AML/CFT supervisory/legal context.
- **[R7] ISO 20022.** “Message Definitions.” https://www.iso20022.org/iso-20022-message-definitions — official message catalogue; check supported version and schema before claiming compliance.
- **[R8] OMG.** “Business Process Model and Notation (BPMN), Version 2.0.2.” https://www.omg.org/spec/BPMN/2.0.2 — official BPMN standard.
- **[R9] NIST.** “SP 800-218, Secure Software Development Framework v1.1.” https://csrc.nist.gov/pubs/sp/800/218/final — optional design/secure-development practice.
- **[R10] ICC.** “Uniform Customs and Practice for Documentary Credits, UCP 600.” https://library.iccwbo.org/content/tfb/RULES/tfb-ucp600-rules.htm — documentary-credit context **not** governing all open-account trades.
- **[R11] HKMA.** “Project CargoX — Recommendation Report.” https://cdi.hkma.gov.hk/wp-content/uploads/Project_CargoX_Recommendation_Report.pdf — HK 2024 trade-finance gap estimate HK$311.2bn–519.1bn. Verify source page and method if reproduced in a chart.
- **[R12] HKMA (7 May 2026).** “HKMA launches CargoX Pilot Programme.” https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/05/20260507-7/ — 21 participating banks and trade/cargo data pilot.
- **[R13] HKMA (Oct 2025).** “e-HKD Pilot Programme: Phase 2 Report.” https://www.hkma.gov.hk/media/eng/doc/key-information/press-release/2025/20251028e4a1.pdf — different forms of money, study themes and institutional wholesale priority.

**Reference execution rule:** For every extracted number use the specific referenced document and date. Prefer citing a stable official page over a secondary article. Re-check accessibility and relevance before final submission; an official link being available is not proof of a team's simulation performance.

---

# FINAL MASTER ACCEPTANCE CHECKLIST

- [ ] Read the official 10-page submitted proposal and course outline; preserve scope.
- [ ] Resolve/record assumptions about HKD denominated mock deposit and Thai-bank observation.
- [ ] Build correct seven-role access policy with server-side checks.
- [ ] Create two semantically correct BPMN workflows.
- [ ] Implement the six-state escrow engine and three current release gates.
- [ ] Implement money conservation, duplicate-command safety, audit evidence and safe AML holds.
- [ ] Execute and export the three flagship cases plus meaningful negative/role tests.
- [ ] Provide a clearly labelled comparator with equivalent step/time definitions and pre-funding trade-off.
- [ ] Complete actual peer feedback, or transparently document its absence.
- [ ] Create a bounded conceptual e-HKD two-leg illustration and scope warning.
- [ ] Capture real running-app screenshots and reproducible raw result files.
- [ ] Deliver interim update with an honest dated progress calculation and next steps.
- [ ] Generate the final report with authentic individual reflections, valid references and under-limit body.
- [ ] Generate final editable presentation slides and demo fallback entirely consistent with actual results.
- [ ] Meet official deadlines, maintain academic-integrity/AI acknowledgements and retain submission receipts.

**End of guidance. Execution models should now work from this single document and produce evidence-backed files, not additional speculative plans.**
