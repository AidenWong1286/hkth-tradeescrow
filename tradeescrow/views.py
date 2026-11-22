"""Role-based read models (least-privilege projections) and audit export.

Visibility is enforced here, server-side, for both the UI and exports. Each
role sees only the field groups listed in VISIBILITY, and only for trades it is
a party to (except Bank H and the regulator, whose scope is the escrow bank's
book). Denied reads are themselves logged to the journal.
"""
from __future__ import annotations

import json

from .escrow import EscrowService
from .model import AccessDenied, Role
from .store import transaction

FIELD_GROUPS = {
    "identity": ["trade_id", "escrow_id", "buyer_id", "seller_id", "issuer_bank_id", "recipient_bank_id"],
    "amount": ["currency", "amount_minor"],
    "commercial_terms": ["contract_terms", "invoice_id", "goods_summary"],
    "logistics_refs": ["shipment_id", "bill_of_lading_id"],
    "customs_refs": ["customs_declaration_id"],
}

# role -> (field groups, extra capabilities)
VISIBILITY = {
    Role.IMPORTER: {"groups": ["identity", "amount", "commercial_terms", "logistics_refs", "customs_refs"],
                    "documents": True, "attestation_detail": "status", "events": "full_own", "balances": "own"},
    Role.EXPORTER: {"groups": ["identity", "amount", "commercial_terms", "logistics_refs", "customs_refs"],
                    "documents": True, "attestation_detail": "status", "events": "full_own", "balances": "own"},
    Role.BANK_HK: {"groups": list(FIELD_GROUPS), "documents": True, "attestation_detail": "full",
                   "events": "full", "balances": "all"},
    Role.BANK_HK_COMPLIANCE: {"groups": list(FIELD_GROUPS), "documents": True, "attestation_detail": "full",
                              "events": "full", "balances": "all"},
    Role.BANK_TH: {"groups": ["identity", "amount", "logistics_refs"], "documents": False,
                   "attestation_detail": "status", "events": "metadata", "balances": "none"},
    Role.LOGISTICS: {"groups": ["identity", "logistics_refs"], "documents": False,
                     "attestation_detail": "own_type:SHIPMENT", "events": "none", "balances": "none"},
    Role.CUSTOMS: {"groups": ["identity", "logistics_refs", "customs_refs"], "documents": False,
                   "attestation_detail": "own_type:CUSTOMS", "events": "none", "balances": "none"},
    Role.REGULATOR: {"groups": ["identity", "amount"], "documents": False, "attestation_detail": "compliance",
                     "events": "metadata", "balances": "none"},
}

EVENT_METADATA_FIELDS = ["event_id", "ts", "actor_role", "actor_kind", "operation", "outcome", "prior_state",
                         "new_state", "reason_code", "related_attestation_ids", "amount_minor", "prev_hash", "hash"]


def _in_scope(svc: EscrowService, role: str, entity: str, trade: dict) -> bool:
    if role == Role.IMPORTER:
        return trade["buyer_id"] == entity
    if role == Role.EXPORTER:
        return trade["seller_id"] == entity
    if role == Role.BANK_TH:
        return trade["recipient_bank_id"] == entity
    if role in (Role.BANK_HK, Role.BANK_HK_COMPLIANCE, Role.REGULATOR, Role.LOGISTICS, Role.CUSTOMS):
        # logistics/customs see any trade on the book but only their reference fields
        return True
    return False


def _deny(svc: EscrowService, actor_id: str, role: str, trade_id: str, what: str):
    with transaction(svc.conn) as c:
        esc = svc._escrow(c, trade_id)
        svc._event(c, trade_id, esc["escrow_id"] if esc else None, actor_id, role,
                   "HUMAN" if role in Role.BUSINESS else "SERVICE", "READ", "REJECTED",
                   esc["state"] if esc else None, esc["state"] if esc else None, "ACCESS_DENIED", [], None,
                   {"attempted": what})
    raise AccessDenied("ACCESS_DENIED", f"{role} may not read {what} for {trade_id}")


def visible_trade_ids(svc: EscrowService, actor_id: str) -> list[str]:
    p = svc.principal(actor_id)
    if p.role not in VISIBILITY:
        return []
    return [t for t in svc.trade_ids() if _in_scope(svc, p.role, p.entity_id, svc.trade(t))]


def trade_view(svc: EscrowService, actor_id: str, trade_id: str) -> dict:
    p = svc.principal(actor_id)
    pol = VISIBILITY.get(p.role)
    trade = svc.trade(trade_id)
    if pol is None or not _in_scope(svc, p.role, p.entity_id, trade):
        _deny(svc, actor_id, p.role, trade_id, "trade_view")
    fields = [f for g in pol["groups"] for f in FIELD_GROUPS[g]]
    view = {f: trade.get(f) for f in fields if f in trade}
    esc = svc.escrow_row(trade_id)
    view["state"] = esc["state"]
    if "amount" in pol["groups"]:
        view["locked_minor"] = esc["locked_minor"]
    # attestation summaries
    atts = svc.attestations(trade_id)
    mode = pol["attestation_detail"]
    if mode == "full":
        view["attestations"] = atts
    elif mode == "status":
        view["attestations"] = [{k: a[k] for k in ("attestation_id", "type", "checkpoint", "result", "issued_at",
                                                     "expires_at", "revoked", "issuer_role")} for a in atts]
    elif mode == "compliance":
        view["attestations"] = [{k: a[k] for k in ("attestation_id", "type", "checkpoint", "result", "reason_code",
                                                     "issued_at", "expires_at", "revoked", "issuer_role")} for a in atts]
    elif mode.startswith("own_type:"):
        t = mode.split(":", 1)[1]
        view["attestations"] = [{k: a[k] for k in ("attestation_id", "type", "result", "issued_at")}
                                for a in atts if a["type"] == t]
    if pol["documents"]:
        view["documents"] = svc.documents(trade_id)
    else:
        view["documents"] = [{"doc_type": d["doc_type"], "revision": d["revision"], "digest": d["digest"]}
                             for d in svc.documents(trade_id)] if p.role == Role.REGULATOR else []
    if pol["balances"] == "own":
        view["my_balance_minor"] = svc.balance(p.entity_id)
    elif pol["balances"] == "all":
        view["balances"] = {a["account_id"]: a["balance_minor"] for a in svc.accounts()}
    if p.role in (Role.BANK_HK, Role.BANK_HK_COMPLIANCE, Role.REGULATOR):
        view["holds"] = [{k: h[k] for k in ("hold_id", "status", "reason_code", "source", "raised_at",
                                            "resolved_at", "decision", "review_reference")} for h in svc.holds(trade_id)]
    if p.role in (Role.BANK_HK, Role.BANK_HK_COMPLIANCE):
        view["release_guard"] = svc.release_guard(trade_id)
    return view


def audit_export(svc: EscrowService, actor_id: str, trade_id: str) -> list[dict]:
    """Role-filtered event history. Regulator & Bank O receive metadata only
    (no commercial document values, no counterparty-identifying details)."""
    p = svc.principal(actor_id)
    pol = VISIBILITY.get(p.role)
    trade = svc.trade(trade_id)
    if pol is None or pol["events"] == "none" or not _in_scope(svc, p.role, p.entity_id, trade):
        _deny(svc, actor_id, p.role, trade_id, "audit_export")
    evs = svc.events(trade_id)
    if pol["events"] in ("full", "full_own"):
        return evs
    out = []
    for e in evs:
        m = {k: e[k] for k in EVENT_METADATA_FIELDS}
        d = e["details"]
        # keep only non-commercial control metadata
        safe = {}
        for k in ("checkpoint", "hold_id", "source", "review_reference", "expires_at", "doc_type", "revision",
                  "attempted", "assigned_reviewer_role", "result"):
            if k in d:
                safe[k] = d[k]
        if "findings" in d:
            safe["finding_codes"] = sorted({f.get("code", f.get("rule")) for f in d["findings"]})
            safe["finding_fields"] = sorted({x for f in d["findings"] for x in f.get("fields", [f.get("field")]) if x})
        if "guard" in d:
            safe["guard_gates"] = [{"gate": g["gate"], "ok": g["ok"]} for g in d["guard"]["gates"]]
        m["details"] = safe
        out.append(m)
    return out


def redaction_probe(export: list[dict], forbidden_values: list) -> list:
    """Return any forbidden value that leaks into an export (used by tests)."""
    blob = json.dumps(export, default=str)
    return [v for v in forbidden_values if str(v) in blob]


def ledger_view(svc: EscrowService, actor_id: str) -> dict:
    """Role-aware projection for the 'Ledger & integrity' page (both UIs use this; neither
    UI may call svc.accounts()/svc.events() directly for display).

    * Bank H operations / compliance: every token account, the full journal, supply and hash-chain detail.
    * Importer / exporter: only accounts they own, pass/fail integrity flags, events for their own trades.
    * Regulator and Bank O: pass/fail integrity flags and metadata-only events for in-scope trades (no balances).
    * Logistics, customs: denied; the attempt is logged as READ REJECTED.
    """
    p = svc.principal(actor_id)
    pol = VISIBILITY.get(p.role)
    if pol is None or (pol["balances"] == "none" and pol["events"] != "metadata"):
        _deny(svc, actor_id, p.role, None, "ledger_view")
    supply, journal = svc.supply_check(), svc.verify_journal()
    out = {"scope": pol["balances"], "role": p.role,
           "integrity": {"conservation_ok": supply["ok"], "hash_chain_ok": journal["ok"]}}
    if pol["balances"] == "all":
        out.update(scope="full", accounts=svc.accounts(), supply=supply, journal=journal, events=svc.events())
        return out
    trades = visible_trade_ids(svc, actor_id)
    if pol["balances"] == "own":
        out["scope"] = "own"
        out["accounts"] = [a for a in svc.accounts() if a["owner_id"] == p.entity_id]
        out["events"] = [e for t in trades for e in svc.events(t)]
    else:  # regulator: metadata only, no balances
        out["scope"] = "metadata"
        out["accounts"] = []
        out["events"] = [e for t in trades for e in audit_export(svc, actor_id, t)]
    out["events"].sort(key=lambda e: (e["ts"], e["event_id"]))
    return out
