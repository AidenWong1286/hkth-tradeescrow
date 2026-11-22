"""UI-neutral action catalogue shared by the Flask console and the Streamlit app.

Each action maps a button to ONE service command, executed AS THE PARTICIPANT
SELECTED IN THE UI (``actor_id``), so the actor recorded in the hash-chained
journal is always the principal being demonstrated. The UI never sets state
directly; authorisation is still enforced by the service (so a role that is
offered a 'forbidden' demo button is refused server-side and the refusal is logged).

Where Bank H operations or compliance press a button that runs a simulated
off-chain service (document matching, KYC/AML screening) or triggers the
guarded release, the human officer is recorded as the initiator; the service's
PERMISSIONS table explicitly allows BANK_HK / BANK_HK_COMPLIANCE for these commands.
"""
from __future__ import annotations

import copy

from .model import Role
from .scenarios import (BANK, BANK_TH, COMPLIANCE, CUSTOMS, EXPORTER, IMPORTER, LOGISTICS, REGULATOR,
                        load_fixture)

VARIANTS = {
    "clean": "TC-001 clean trade (all checks pass)",
    "mismatch": "TC-002 invoice amount HKD 245,000 vs contract HKD 250,000",
    "aml": "TC-003 exporter hits synthetic watchlist before pre-release screening",
}


def variant_fixture(variant: str) -> dict:
    fx = load_fixture()
    if variant == "mismatch":
        fx["invoice"]["amount_minor"] = 24_500_000
    return fx


# action_id -> (label, default principal used by autoplay / docs, help)
ACTIONS = {
    "create": ("Create & fund escrow", IMPORTER, "Creation KYC/AML, limit & balance check, lock HKD 250,000 tokens"),
    "dispute_imp": ("Raise dispute", IMPORTER, "Moves Created/Pending escrow to Under Review"),
    "invoice": ("Submit commercial invoice", EXPORTER, "Uses the selected scenario's invoice"),
    "bl": ("Submit bill of lading", EXPORTER, ""),
    "invoice_fix": ("Submit corrected invoice", EXPORTER, "New revision with contract amount; invalidates old approvals"),
    "exp_try_clear": ("Try to clear AML hold (forbidden)", EXPORTER, "Demonstrates server-side RBAC refusal"),
    "customs": ("Submit export customs declaration", CUSTOMS, ""),
    "ship": ("Attest shipped on board (SH-001)", LOGISTICS, "Off-chain shipment attestation"),
    "ship_wrong": ("Attest shipment SH-002 (wrong trade)", LOGISTICS, "Negative test: cross-trade evidence"),
    "doc_check": ("Run document matching", BANK, "Executes the simulated document-matching service"),
    "revalidate": ("Reviewer: revalidate documents", BANK, "Under Review -> Pending (needs fresh doc PASS)"),
    "terminate_review": ("Reviewer: terminate & refund", BANK, "Under Review -> Refunded/Terminated"),
    "settle_bank": ("Trigger contract release", BANK, "Guarded release; refused unless all gates pass"),
    "screen": ("Run pre-release KYC/AML screening", COMPLIANCE, "Executes the simulated screening service"),
    "hold": ("Raise manual compliance hold", COMPLIANCE, ""),
    "clear": ("Clear hold (false positive)", COMPLIANCE, "Frozen -> Pending/Created/Under Review; never direct release"),
    "terminate_hold": ("Confirm alert: terminate & refund", COMPLIANCE, "Frozen -> Refunded/Terminated"),
    "ack": ("Acknowledge receipt (observation)", BANK_TH, "No real THB credit"),
    "reg_try_release": ("Try to release funds (forbidden)", REGULATOR, "Demonstrates read-only regulator"),
}

ROLE_ACTIONS = {
    Role.IMPORTER: ["create", "dispute_imp"],
    Role.EXPORTER: ["invoice", "bl", "invoice_fix", "exp_try_clear"],
    Role.CUSTOMS: ["customs"],
    Role.LOGISTICS: ["ship", "ship_wrong"],
    Role.BANK_HK: ["doc_check", "revalidate", "terminate_review", "settle_bank"],
    Role.BANK_HK_COMPLIANCE: ["screen", "hold", "clear", "terminate_hold"],
    Role.BANK_TH: ["ack"],
    Role.REGULATOR: ["reg_try_release"],
}

_counter = {"n": 0}


def run_action(svc, action: str, variant: str, actor_id: str, trade_id: str = "TR-001"):
    """Run one catalogue action as ``actor_id`` (the participant selected in the UI)."""
    if action not in ACTIONS:
        raise KeyError(action)
    a = actor_id
    fx = variant_fixture(variant)
    t = trade_id
    _counter["n"] += 1
    ref = f"UI-{_counter['n']:04d}"
    if action == "create":
        return svc.create_escrow(a, fx["trade"], fx["contract"])
    if action == "dispute_imp":
        return svc.raise_dispute(a, t, "importer reports discrepancy (demo)")
    if action == "invoice":
        return svc.submit_document(a, t, "INVOICE", fx["invoice"])
    if action == "bl":
        return svc.submit_document(a, t, "BILL_OF_LADING", fx["bill_of_lading"])
    if action == "invoice_fix":
        return svc.submit_document(a, t, "INVOICE", dict(fx["invoice"], amount_minor=fx["trade"]["amount_minor"]))
    if action == "exp_try_clear":
        return svc.resolve_hold(a, t, "CLEAR", "SELF-APPROVAL")
    if action == "customs":
        return svc.submit_document(a, t, "CUSTOMS_DECLARATION", fx["customs_declaration"])
    if action == "ship":
        return svc.attest_shipment(a, t, fx["shipment_event"])
    if action == "ship_wrong":
        return svc.attest_shipment(a, t, dict(fx["shipment_event"], shipment_id="SH-002", trade_id="TR-002"))
    if action == "doc_check":
        return svc.run_document_check(a, t)
    if action == "revalidate":
        return svc.resolve_review(a, t, "REVALIDATE", f"REV-{ref}", "corrected documents verified")
    if action == "terminate_review":
        return svc.resolve_review(a, t, "TERMINATE", f"REV-{ref}", "dispute unresolved")
    if action == "settle_bank":
        return svc.settle(a, t)
    if action == "screen":
        return svc.run_screening(a, t, "PRE_RELEASE")
    if action == "hold":
        return svc.raise_hold(a, t, "MANUAL_COMPLIANCE_HOLD", ["exporter_th_01"])
    if action == "clear":
        return svc.resolve_hold(a, t, "CLEAR", f"AML-{ref}", "false positive after review")
    if action == "terminate_hold":
        return svc.resolve_hold(a, t, "TERMINATE", f"AML-{ref}", "alert confirmed (simulated)")
    if action == "ack":
        return svc.acknowledge_receipt(a, t)
    if action == "reg_try_release":
        return svc.settle(a, t)
    raise KeyError(action)


def autoplay_steps(variant: str) -> list[tuple[str, str]]:
    """(principal, action) sequences for one-click demo replays."""
    base = [(IMPORTER, "create"), (CUSTOMS, "customs"), (LOGISTICS, "ship"), (EXPORTER, "invoice"),
            (EXPORTER, "bl"), (BANK, "doc_check")]
    if variant == "clean":
        return base + [(COMPLIANCE, "screen"), (BANK, "settle_bank"), (BANK_TH, "ack")]
    if variant == "mismatch":
        return base + [(BANK, "settle_bank"), (EXPORTER, "invoice_fix"), (BANK, "doc_check"),
                       (BANK, "revalidate"), (COMPLIANCE, "screen"), (BANK, "settle_bank")]
    return base + [("sim", "inject_aml"), (COMPLIANCE, "screen"), (BANK, "settle_bank"),
                   (COMPLIANCE, "clear"), (COMPLIANCE, "screen"), (BANK, "settle_bank")]


def run_autoplay(svc, variant: str) -> list:
    """Replay a scenario on ``svc``; every step runs as the explicit principal in autoplay_steps()."""
    results = []
    for who, action in autoplay_steps(variant):
        svc.clock.advance(hours=2)
        if action == "inject_aml":
            svc.sim_add_watchlist("exporter_th_01", "SANCTIONS_FLAG_SIMULATED")
        else:
            results.append((who, action, run_action(svc, action, variant, who)))
    return results


def run_autoplay_step(svc, variant: str, i: int):
    """Run step ``i`` of autoplay_steps(variant) exactly as run_autoplay() does (film mode in the
    Flask console). Returns (principal, action, CommandResult or None for the simulation step)."""
    who, action = autoplay_steps(variant)[i]
    svc.clock.advance(hours=2)
    if action == "inject_aml":
        svc.sim_add_watchlist("exporter_th_01", "SANCTIONS_FLAG_SIMULATED")
        return who, action, None
    return who, action, run_action(svc, action, variant, who)


def fmt_hkd(minor) -> str:
    return "—" if minor is None else f"HKD {minor/100:,.2f}"


def copy_fixture(fx):
    return copy.deepcopy(fx)
