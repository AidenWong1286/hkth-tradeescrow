# Domain model and money accounting

## Instruments (never conflated)
| Instrument | Meaning in the prototype | Real-world analogue (not implemented) |
|---|---|---|
| `TDEP-HKD@bank_hk_h` | Simulated tokenised **commercial-bank deposit**: a claim on Bank H, HKD, integer cents | Bank-issued tokenised deposit (e.g. EnsembleTX participants) |
| CeBM leg (e-HKD extension only) | Simulated **central-bank money**: interbank settlement asset | Tokenised CeBM / wholesale e-HKD concept |
| Trade denomination | HKD only (single currency; `UNSUPPORTED_CURRENCY` otherwise) | Real corridor would need FX, THB legs |

Bank O (Thailand) **observes and acknowledges** releases; no THB credit, FX or cross-bank finality is modelled.

## Accounts and conservation invariant
Holder accounts: importer, exporter, and one escrow account per escrow (`escrow:ESC-xxx`). All supply is
issued once at setup (`ISSUE` events). For every state of the ledger:

`Σ holder balances = issued supply`, no negative balance (SQL CHECK), `escrow account balance = escrows.locked_minor`,
and replaying all postings reproduces every balance. Lock = importer→escrow; release = escrow→exporter;
refund = escrow→importer. Each transfer is one posting, written in the same transaction as the state change and journal event.

## Entities (SQLite tables)
`trades`, `escrows(state, locked_minor, version)`, `accounts`, `postings`, `documents(doc_type, revision, digest)`,
`attestations(type, checkpoint, result, issued_at, expires_at, input_digest, revoked, seq)`,
`holds(status ACTIVE/CLEARED/RESOLVED_TERMINATE, raised_seq)`, `events` (hash-chained journal), `commands` (idempotency),
`parties`, `watchlist`, `dispositions` (false-positive decisions).

## Attestation semantics
* **SHIPMENT**: issued by LOGISTICS; `subject_id` must equal the trade's `shipment_id`, otherwise `CROSS_TRADE_EVIDENCE`.
* **DOCUMENTS**: issued by the document service; `input_digest` = hash of the latest revision digests of all four documents.
  Any new revision revokes prior DOCUMENTS attestations, and the guard also re-checks the digest (defence in depth).
* **KYC_AML**: checkpoints `CREATION` (must PASS to create), `PRE_RELEASE` (PASS valid for 48 h; must be newer than
  the latest document approval and the latest hold) and `ONGOING`. ALERT/FAIL opens a hold and freezes the escrow.
* A missing attestation is never a PASS. Revision ties are resolved by the strict integer revision counter, not by timestamp.

## Role permissions (commands)
| Command | Allowed roles |
|---|---|
| create_escrow | IMPORTER (must be the trade's buyer) |
| submit_document | EXPORTER (invoice, B/L; must be the seller), IMPORTER (contract), CUSTOMS (declaration) |
| attest_shipment | LOGISTICS |
| run_document_check | SVC_DOCUMENTS, BANK_HK |
| run_screening | SVC_COMPLIANCE, BANK_HK_COMPLIANCE |
| raise_hold / resolve_hold | BANK_HK_COMPLIANCE |
| raise_dispute | IMPORTER, EXPORTER (own trade), BANK_HK |
| resolve_review | BANK_HK |
| settle (release) | SYSTEM_CONTRACT, BANK_HK (trigger only; the guard decides) |
| acknowledge_receipt | BANK_TH (recipient bank of the trade) |
| REGULATOR | **no state-changing command** (read-only audit) |

## Visibility (read models)
| Role | Trade fields | Document bodies | Compliance reason codes | Audit trail |
|---|---|---|---|---|
| Importer / Exporter (own trade only) | all commercial | yes | status only | full, own trade |
| Bank H ops / compliance | all | yes | yes + guard + holds | full |
| Bank O | identity, amount, logistics refs | no | status only | metadata only |
| Logistics | identity, shipment refs | no | own SHIPMENT only | none |
| Customs | identity, shipment and customs refs | no | none | none |
| Regulator | identity (entity IDs), amount | digests only | yes | **metadata only** (no document values, no user IDs) |
Denied reads and denied commands are logged (`READ`/`<OP>` with outcome `REJECTED`).
