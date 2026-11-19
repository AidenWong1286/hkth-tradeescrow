# Limitations and real-deployment risks

| Area | Limitation in the prototype | What a real deployment would need |
|---|---|---|
| Legal status of tokenised deposits | Synthetic claim on "Bank H"; no deposit terms, insolvency treatment or deposit protection | Legal opinion on ownership, segregation of escrowed tokens, insolvency remoteness |
| Settlement finality | Database commit ≠ legal finality; Bank O only "observes" | Designated system / finality rules; interbank leg in CeBM |
| Oracle / attestation trust | Logistics, document and screening modules are mocks; the contract cannot know goods shipped or are as described | Signed attestations, issuer accountability, eB/L standards, revocation, dispute evidence |
| Compliance accountability | KYC/AML PASS/ALERT are simulation inputs; no STR filing, sanctions list, tipping-off control | Bank's AML/CFT programme; regulatory reporting; human investigation SLAs |
| Dispute handling | Termination refunds the importer under a simple rule; no partial release, quality disputes, arbitration | Contractual dispute clauses, partial release, governing law, arbitration |
| AML terminate policy | Confirmed alerts refund the importer; in reality funds may need to be held or reported | Policy aligned with legal obligations |
| Liquidity / pre-funding | Importer cash is locked from funding to release (7.5 base-case days, normal scenario) | Pricing of lock-up; possible bank financing of the escrow; interest on escrow |
| Privacy & access governance | Role projections are code-level, not cryptographic; regulator scope is a design choice | Data-protection review (PDPO, Thai PDPA), access logs, consent |
| Operational resilience | Single SQLite file; one process; no HA, backup or key management | Permissioned DLT or resilient DB, BCP, cyber controls |
| DLT claims | Hash chain is tamper-evident only; no consensus, no independent nodes | Governance of nodes, validators, upgrade rights |
| Interoperability | HKD only, no FX, no ISO 20022 schema validation (mock fields only) | Schema-valid messages, multi-currency, platform interoperability ("digital islands") |
| Evidence base | Durations are assumptions; no real users; peer feedback pending | Pilot data, user research |
| UI | Role switching is a demo control, not authentication | Real identity, MFA, authorisation service |
