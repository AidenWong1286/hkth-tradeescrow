"""Simulated off-chain attestation modules.

These are deterministic rule functions standing in for real-world sources:
  * document matching (bank document checker / trade-data platform)
  * KYC/AML screening (bank compliance systems)
The escrow contract never "sees" the real world: it only consumes the
attestations these modules emit. Their outputs are simulation inputs, not
regulatory clearance.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

REQUIRED_DOCS = ("CONTRACT", "INVOICE", "BILL_OF_LADING", "CUSTOMS_DECLARATION")

REQUIRED_FIELDS = {
    "CONTRACT": ("contract_id", "buyer_id", "seller_id", "goods_description", "hs_code",
                 "quantity", "unit", "amount_minor", "currency", "incoterm",
                 "port_of_loading", "port_of_discharge", "latest_shipment_date"),
    "INVOICE": ("invoice_id", "buyer_id", "seller_id", "goods_description", "hs_code",
                "quantity", "amount_minor", "currency", "issue_date"),
    "BILL_OF_LADING": ("bl_id", "shipment_id", "shipper_id", "consignee_id", "goods_description",
                       "quantity", "port_of_loading", "port_of_discharge", "on_board_date", "vessel"),
    "CUSTOMS_DECLARATION": ("declaration_id", "exporter_id", "hs_code", "goods_description",
                            "quantity", "declared_value_minor", "currency", "port"),
}


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def _norm(v: Any) -> Any:
    return " ".join(v.lower().split()) if isinstance(v, str) else v


def match_documents(trade: dict, docs: dict[str, dict]) -> dict:
    """Field-based consistency check across contract, invoice, bill of lading and
    customs declaration. Returns {result, reason_code, findings[]}.

    result = PASS | FAIL | PENDING (a required document has not been submitted).
    """
    missing_docs = [d for d in REQUIRED_DOCS if d not in docs]
    if missing_docs:
        return {"result": "PENDING", "reason_code": "DOC_NOT_YET_SUBMITTED",
                "findings": [{"rule": "presence", "doc": d} for d in missing_docs]}

    findings: list[dict] = []
    for dtype, fields in REQUIRED_FIELDS.items():
        for f in fields:
            v = docs[dtype].get(f)
            if v is None or v == "":
                findings.append({"rule": "required_field", "code": "DOC_MISSING_FIELD",
                                 "field": f"{dtype}.{f}"})

    c, inv, bl, cus = (docs["CONTRACT"], docs["INVOICE"], docs["BILL_OF_LADING"],
                       docs["CUSTOMS_DECLARATION"])

    def same(code: str, pairs: list[tuple[str, Any]]):
        vals = [(name, _norm(v)) for name, v in pairs if v not in (None, "")]
        if len({canonical(v) for _, v in vals}) > 1:
            findings.append({"rule": "cross_document", "code": code,
                             "fields": [n for n, _ in vals],
                             "values": {n: v for n, v in vals}})

    same("DOC_AMOUNT_MISMATCH", [("TRADE.amount_minor", trade["amount_minor"]),
                                 ("CONTRACT.amount_minor", c.get("amount_minor")),
                                 ("INVOICE.amount_minor", inv.get("amount_minor"))])
    same("DOC_VALUE_MISMATCH", [("INVOICE.amount_minor", inv.get("amount_minor")),
                                ("CUSTOMS_DECLARATION.declared_value_minor", cus.get("declared_value_minor"))])
    same("DOC_CURRENCY_MISMATCH", [("TRADE.currency", trade["currency"]),
                                   ("INVOICE.currency", inv.get("currency")),
                                   ("CUSTOMS_DECLARATION.currency", cus.get("currency"))])
    same("DOC_QUANTITY_MISMATCH", [("CONTRACT.quantity", c.get("quantity")),
                                   ("INVOICE.quantity", inv.get("quantity")),
                                   ("BILL_OF_LADING.quantity", bl.get("quantity")),
                                   ("CUSTOMS_DECLARATION.quantity", cus.get("quantity"))])
    same("DOC_GOODS_MISMATCH", [("CONTRACT.goods_description", c.get("goods_description")),
                                ("INVOICE.goods_description", inv.get("goods_description")),
                                ("BILL_OF_LADING.goods_description", bl.get("goods_description")),
                                ("CUSTOMS_DECLARATION.goods_description", cus.get("goods_description"))])
    same("DOC_HS_CODE_MISMATCH", [("CONTRACT.hs_code", c.get("hs_code")),
                                  ("INVOICE.hs_code", inv.get("hs_code")),
                                  ("CUSTOMS_DECLARATION.hs_code", cus.get("hs_code"))])
    same("DOC_INVOICE_REF_MISMATCH", [("TRADE.invoice_id", trade["invoice_id"]),
                                      ("INVOICE.invoice_id", inv.get("invoice_id"))])
    same("DOC_BL_REF_MISMATCH", [("TRADE.bill_of_lading_id", trade["bill_of_lading_id"]),
                                 ("BILL_OF_LADING.bl_id", bl.get("bl_id"))])
    same("DOC_SHIPMENT_REF_MISMATCH", [("TRADE.shipment_id", trade["shipment_id"]),
                                       ("BILL_OF_LADING.shipment_id", bl.get("shipment_id"))])
    same("DOC_CUSTOMS_REF_MISMATCH", [("TRADE.customs_declaration_id", trade["customs_declaration_id"]),
                                      ("CUSTOMS_DECLARATION.declaration_id", cus.get("declaration_id"))])
    same("DOC_BUYER_MISMATCH", [("TRADE.buyer_id", trade["buyer_id"]),
                                ("CONTRACT.buyer_id", c.get("buyer_id")),
                                ("INVOICE.buyer_id", inv.get("buyer_id")),
                                ("BILL_OF_LADING.consignee_id", bl.get("consignee_id"))])
    same("DOC_SELLER_MISMATCH", [("TRADE.seller_id", trade["seller_id"]),
                                 ("CONTRACT.seller_id", c.get("seller_id")),
                                 ("INVOICE.seller_id", inv.get("seller_id")),
                                 ("BILL_OF_LADING.shipper_id", bl.get("shipper_id")),
                                 ("CUSTOMS_DECLARATION.exporter_id", cus.get("exporter_id"))])
    same("DOC_PORT_MISMATCH", [("CONTRACT.port_of_loading", c.get("port_of_loading")),
                               ("BILL_OF_LADING.port_of_loading", bl.get("port_of_loading")),
                               ("CUSTOMS_DECLARATION.port", cus.get("port"))])
    same("DOC_PORT_MISMATCH", [("CONTRACT.port_of_discharge", c.get("port_of_discharge")),
                               ("BILL_OF_LADING.port_of_discharge", bl.get("port_of_discharge"))])
    if bl.get("on_board_date") and c.get("latest_shipment_date") and \
            bl["on_board_date"] > c["latest_shipment_date"]:
        findings.append({"rule": "contract_condition", "code": "DOC_LATE_SHIPMENT",
                         "fields": ["BILL_OF_LADING.on_board_date", "CONTRACT.latest_shipment_date"],
                         "values": {"BILL_OF_LADING.on_board_date": bl["on_board_date"],
                                    "CONTRACT.latest_shipment_date": c["latest_shipment_date"]}})

    if findings:
        return {"result": "FAIL", "reason_code": findings[0]["code"], "findings": findings}
    return {"result": "PASS", "reason_code": "DOCS_CONSISTENT", "findings": []}


def screen_parties(parties: dict[str, dict], party_ids: list[str], trade: dict,
                   watchlist: list[dict], dispositions: set[tuple[str, str]], now_iso: str) -> dict:
    """Mock KYC/AML screening. Deterministic rules over a synthetic registry:

    FAIL  KYC_NOT_VERIFIED / KYC_EXPIRED            (customer due diligence not current)
    ALERT SANCTIONS_FLAG_SIMULATED / other watchlist reason (active synthetic watchlist hit)
    ALERT TXN_PROFILE_ALERT_SIMULATED               (amount above the party's declared profile)
    Alerts with a recorded false-positive disposition are suppressed.
    """
    hits: list[dict] = []
    for pid in party_ids:
        p = parties.get(pid)
        if p is None or p.get("kyc_status") != "VERIFIED":
            hits.append({"party_id": pid, "result": "FAIL", "code": "KYC_NOT_VERIFIED"})
            continue
        if p.get("kyc_valid_until") and p["kyc_valid_until"] < now_iso[:10]:
            hits.append({"party_id": pid, "result": "FAIL", "code": "KYC_EXPIRED"})
        for w in watchlist:
            if w["party_id"] == pid and w["active"] and (pid, w["reason_code"]) not in dispositions:
                hits.append({"party_id": pid, "result": "ALERT", "code": w["reason_code"]})
        limit = p.get("expected_max_trade_minor")
        if limit and trade["amount_minor"] > limit and \
                (pid, "TXN_PROFILE_ALERT_SIMULATED") not in dispositions:
            hits.append({"party_id": pid, "result": "ALERT", "code": "TXN_PROFILE_ALERT_SIMULATED"})
    if any(h["result"] == "FAIL" for h in hits):
        first = next(h for h in hits if h["result"] == "FAIL")
        return {"result": "FAIL", "reason_code": first["code"], "hits": hits}
    if hits:
        return {"result": "ALERT", "reason_code": hits[0]["code"], "hits": hits}
    return {"result": "PASS", "reason_code": "SCREENING_CLEAR", "hits": []}
