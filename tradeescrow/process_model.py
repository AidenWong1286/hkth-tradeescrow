"""Single source of truth for the two comparable process models.

The same definitions generate (a) diagrams/baseline.bpmn and diagrams/proposed.bpmn,
(b) the rendered swimlane figures, and (c) the step/manual-effort/time metrics.

ALL DURATIONS ARE TEAM ASSUMPTIONS (illustrative low/base/high, in calendar days),
fixed before running the comparison. They are not empirical measurements of real
open-account or escrow transactions.

Task attributes
  kind     MANUAL (a person performs or approves), AUTO (system), EXTERNAL_MANUAL
           (third party: customs/carrier; manual in both models)
  segment  COMMON (same in both models: goods, customs, carriage) or SETTLEMENT
  path     MAIN (happy path) | MISMATCH | AML  (exception sub-paths)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    id: str
    lane: str
    name: str
    kind: str
    segment: str
    dur: tuple[float, float, float]      # low, base, high (days)
    path: str = "MAIN"
    milestone: str | None = None         # SHIPMENT / FUNDED / CREDITED


AUTO_D = (0.0, 0.0, 0.0)  # automated engine steps: simulated as instantaneous in business time

BASELINE_LANES = ["Importer (HK)", "Bank H (importer's bank)", "Bank O (exporter's bank)",
                  "Exporter (TH)", "Logistics / Customs"]
BASELINE = [
    Task("B01", "Exporter (TH)", "Prepare goods & export declaration", "MANUAL", "COMMON", (3, 5, 7)),
    Task("B02", "Logistics / Customs", "Clear export customs", "EXTERNAL_MANUAL", "COMMON", (0.5, 1, 2)),
    Task("B03", "Logistics / Customs", "Load goods & issue bill of lading", "EXTERNAL_MANUAL", "COMMON", (0.5, 1, 2),
         milestone="SHIPMENT"),
    Task("B04", "Exporter (TH)", "Compile invoice & shipping documents", "MANUAL", "SETTLEMENT", (0.5, 1, 2)),
    Task("B05", "Exporter (TH)", "Send documents to importer", "MANUAL", "SETTLEMENT", (0.5, 2, 4)),
    Task("B06", "Importer (HK)", "Check documents against contract", "MANUAL", "SETTLEMENT", (0.5, 1, 2)),
    Task("B06x", "Importer (HK)", "Raise discrepancy; obtain corrected documents", "MANUAL", "SETTLEMENT",
         (2, 3, 5), path="MISMATCH"),
    Task("B07", "Importer (HK)", "Wait for agreed payment term", "WAIT", "SETTLEMENT", (0, 0, 0)),
    Task("B08", "Importer (HK)", "Initiate payment instruction", "MANUAL", "SETTLEMENT", (0.25, 0.5, 1),
         milestone="FUNDED"),
    Task("B09", "Bank H (importer's bank)", "Payment screening & approval", "MANUAL", "SETTLEMENT", (0.25, 1, 2)),
    Task("B09x", "Bank H (importer's bank)", "Compliance investigation of alert", "MANUAL", "SETTLEMENT",
         (2, 3, 5), path="AML"),
    Task("B10", "Bank H (importer's bank)", "Send cross-border payment message", "AUTO", "SETTLEMENT", (0.1, 0.5, 1)),
    Task("B11", "Bank O (exporter's bank)", "Receive, screen & credit exporter", "MANUAL", "SETTLEMENT", (0.25, 1, 2),
         milestone="CREDITED"),
    Task("B12", "Exporter (TH)", "Reconcile receipt against invoice", "MANUAL", "SETTLEMENT", (0.25, 0.5, 1)),
]

PROPOSED_LANES = ["Importer (HK)", "Bank H escrow contract & services", "Bank O (observer)",
                  "Exporter (TH)", "Logistics / Customs", "Regulator (audit)"]
PROPOSED = [
    Task("E01", "Importer (HK)", "Create & fund escrow request", "MANUAL", "SETTLEMENT", (0.25, 0.5, 1)),
    Task("E02", "Bank H escrow contract & services", "Creation KYC/AML screening", "AUTO", "SETTLEMENT", AUTO_D),
    Task("E03", "Bank H escrow contract & services", "Lock tokenised deposits", "AUTO", "SETTLEMENT", AUTO_D,
         milestone="FUNDED"),
    Task("E04", "Exporter (TH)", "Prepare goods & export declaration", "MANUAL", "COMMON", (3, 5, 7)),
    Task("E05", "Logistics / Customs", "Clear export customs; submit declaration", "EXTERNAL_MANUAL", "COMMON",
         (0.5, 1, 2)),
    Task("E06", "Logistics / Customs", "Load goods; issue B/L; attest shipment", "EXTERNAL_MANUAL", "COMMON",
         (0.5, 1, 2), milestone="SHIPMENT"),
    Task("E07", "Exporter (TH)", "Upload invoice & bill of lading", "MANUAL", "SETTLEMENT", (0.1, 0.5, 1)),
    Task("E08", "Bank H escrow contract & services", "Automated 4-document matching", "AUTO", "SETTLEMENT", AUTO_D),
    Task("E08x", "Bank H escrow contract & services", "Manual review; exporter corrects; revalidate", "MANUAL",
         "SETTLEMENT", (2, 3, 5), path="MISMATCH"),
    Task("E09", "Bank H escrow contract & services", "Pre-release KYC/AML screening", "AUTO", "SETTLEMENT", AUTO_D),
    Task("E09x", "Bank H escrow contract & services", "Compliance investigation (Frozen)", "MANUAL", "SETTLEMENT",
         (2, 3, 5), path="AML"),
    Task("E10", "Bank H escrow contract & services", "Guarded release to exporter", "AUTO", "SETTLEMENT", AUTO_D,
         milestone="CREDITED"),
    Task("E11", "Bank O (observer)", "Acknowledge receipt (observation)", "MANUAL", "SETTLEMENT", (0, 0.1, 0.5)),
    Task("E12", "Regulator (audit)", "Read-only audit trail available", "AUTO", "SETTLEMENT", AUTO_D),
]

# sequence (with exception loops) used for BPMN generation
FLOWS = {
    "baseline": [("start", "B01"), ("B01", "B02"), ("B02", "B03"), ("B03", "B04"), ("B04", "B05"), ("B05", "B06"),
                 ("B06", "G1"), ("G1", "B07", "documents consistent"), ("G1", "B06x", "discrepancy"),
                 ("B06x", "B06"), ("B07", "B08"), ("B08", "B09"), ("B09", "G2"), ("G2", "B10", "clear"),
                 ("G2", "B09x", "alert"), ("B09x", "B10", "cleared"), ("B10", "B11"), ("B11", "B12"),
                 ("B12", "end")],
    "proposed": [("start", "E01"), ("E01", "E02"), ("E02", "G0"), ("G0", "E03", "PASS"), ("G0", "end_rej", "FAIL"),
                 ("E03", "E04"), ("E04", "E05"), ("E05", "E06"), ("E06", "E07"), ("E07", "E08"), ("E08", "G1"),
                 ("G1", "E09", "PASS"), ("G1", "E08x", "FAIL → Under Review"), ("E08x", "E09"),
                 ("E09", "G2"), ("G2", "E10", "PASS (fresh, no hold)"), ("G2", "E09x", "ALERT → Frozen"),
                 ("E09x", "E09", "cleared → re-screen"), ("E09x", "end_ref", "terminate → refund"),
                 ("E10", "E11"), ("E11", "E12"), ("E12", "end")],
}
GATEWAYS = {
    "baseline": {"G1": ("Importer (HK)", "Documents OK?"), "G2": ("Bank H (importer's bank)", "Screening alert?")},
    "proposed": {"G0": ("Bank H escrow contract & services", "Creation KYC?"),
                 "G1": ("Bank H escrow contract & services", "Docs PASS?"),
                 "G2": ("Bank H escrow contract & services", "Release guard")},
}
EVENTS = {
    "baseline": {"start": ("Exporter (TH)", "Contract signed"), "end": ("Exporter (TH)", "Payment reconciled")},
    "proposed": {"start": ("Importer (HK)", "Contract signed"), "end": ("Regulator (audit)", "Settled & auditable"),
                 "end_rej": ("Bank H escrow contract & services", "Escrow rejected"),
                 "end_ref": ("Bank H escrow contract & services", "Refunded/Terminated")},
}

# ---------------------------------------------------------------------------------------------
# MATCHED-SCOPE SENSITIVITY VARIANT (audit P1-4). NOT IMPLEMENTED IN THE PROTOTYPE.
# The baseline ends with Bank O crediting the exporter and the exporter reconciling; the prototype
# ends with a synthetic HKD claim on Bank H and a Bank O *observation*. To compare like with like,
# 'proposed_e2e' replaces E11 with the hypothetical steps the escrow would still need to reach the
# same end point. Durations re-use the baseline's own assumptions for the equivalent steps
# (B10, B11, B12), so the variant cannot look better merely by choosing new numbers.
# FX conversion is excluded in BOTH models (single-currency HKD comparison).
PROPOSED_E2E_LANES = PROPOSED_LANES[:2] + ["Bank O (exporter's bank)"] + PROPOSED_LANES[3:]
PROPOSED_E2E = [t for t in PROPOSED if t.id not in ("E10", "E11")] + [
    Task("E10", "Bank H escrow contract & services", "Guarded release to exporter's Bank H token account", "AUTO",
         "SETTLEMENT", AUTO_D, milestone="RELEASED"),
    Task("E13h", "Exporter (TH)", "Instruct redemption & transfer to Bank O (hypothetical)", "MANUAL", "SETTLEMENT",
         (0.1, 0.25, 0.5)),
    Task("E14h", "Bank H escrow contract & services", "Redeem tokens; send cross-border payment (= B10)", "AUTO",
         "SETTLEMENT", (0.1, 0.5, 1)),
    Task("E15h", "Bank O (exporter's bank)", "Receive, screen & credit exporter (= B11)", "MANUAL", "SETTLEMENT",
         (0.25, 1, 2), milestone="CREDITED"),
    Task("E16h", "Exporter (TH)", "Reconcile receipt against invoice (= B12)", "MANUAL", "SETTLEMENT",
         (0.25, 0.5, 1)),
]

MODELS = {"baseline": (BASELINE_LANES, BASELINE), "proposed": (PROPOSED_LANES, PROPOSED)}
SENSITIVITY_MODELS = {"proposed_e2e": (PROPOSED_E2E_LANES, PROPOSED_E2E)}
ALL_MODELS = {**MODELS, **SENSITIVITY_MODELS}
MODEL_LABELS = {"baseline": "Baseline open account",
                "proposed": "Escrow prototype scope (ends at Bank H release; Bank O observes)",
                "proposed_e2e": "Escrow + hypothetical cross-bank leg (matched scope; not implemented)"}
LEVEL = {"low": 0, "base": 1, "high": 2}


def tasks_for(model: str, scenario: str) -> list[Task]:
    """Tasks executed in a scenario class: MAIN plus the matching exception path."""
    _, tasks = ALL_MODELS[model]
    extra = {"normal": set(), "mismatch": {"MISMATCH"}, "aml": {"AML"}}[scenario]
    return [t for t in tasks if t.path == "MAIN" or t.path in extra]


def timeline(model: str, scenario: str, level: str, payment_term_days: float = 0.0) -> dict:
    """Sequential execution under the stated assumptions; returns milestone times (days from contract)."""
    t = 0.0
    marks: dict[str, float] = {}
    for task in tasks_for(model, scenario):
        d = task.dur[LEVEL[level]]
        if task.id == "B07":
            d = payment_term_days
        # exception handling occurs before the payment/release step in both models
        t += d
        if task.milestone:
            marks[task.milestone] = t
    marks["END"] = t
    return marks
