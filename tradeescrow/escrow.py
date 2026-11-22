"""EscrowService: the simulated smart-contract escrow and its service layer.

Every state-changing operation is a *command* that:
  1. runs inside one serialised SQLite transaction (BEGIN IMMEDIATE),
  2. is authorised server-side against PERMISSIONS (role switching in a UI
     cannot bypass it),
  3. either commits its state change + token postings + journal events together,
     or is rolled back and recorded as a REJECTED journal event,
  4. is idempotent when a command_id is supplied (replays return the stored
     result instead of executing twice).

The UI (Flask or Streamlit), the pytest suite and the experiment runner all use
this same class. Nothing here connects to a real bank, ledger or CBDC.
"""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Callable

from . import offchain
from .clock import SimClock, parse
from .model import (DOC_SUBMITTERS, PERMISSIONS, TRANSITIONS, CommandResult, IllegalTransition,
                    Principal, Rejection, Role, State)
from .store import connect, transaction

GENESIS = "0" * 64
INSTRUMENT = "TDEP-HKD@bank_hk_h"   # simulated tokenised commercial-bank deposit issued by Bank H

DEFAULT_CONFIG = {
    "currency": "HKD",
    "txn_limit_minor": 500_000_000,            # synthetic per-trade limit: HKD 5,000,000.00
    "prerelease_kyc_validity_hours": 48,       # freshness window of the pre-release screening
    "escrow_bank_id": "bank_hk_h",
}


def _j(obj: Any) -> str:
    return offchain.canonical(obj)


class EscrowService:
    def __init__(self, db_path: str = ":memory:", clock: SimClock | None = None,
                 config: dict | None = None):
        self.db_path = db_path
        self.conn = connect(db_path)
        self.clock = clock or SimClock()
        self.config = {**DEFAULT_CONFIG, **(config or {})}

    # ------------------------------------------------------------------ setup
    def setup(self, principals: list[dict], parties: list[dict], issuance: dict[str, int]) -> None:
        """Load synthetic principals/parties and issue the fixed token supply.
        Logged as SETUP events so the journal is complete from genesis."""
        with transaction(self.conn) as c:
            for p in principals:
                c.execute("INSERT OR REPLACE INTO principals VALUES(?,?,?,?)",
                          (p["principal_id"], p["role"], p["entity_id"], p.get("display", "")))
            for party in parties:
                c.execute("INSERT OR REPLACE INTO parties VALUES(?,?)", (party["party_id"], _j(party)))
            total = 0
            for owner, amount in issuance.items():
                acct = self._acct(owner)
                c.execute("INSERT OR IGNORE INTO accounts VALUES(?,?,?,0)", (acct, owner, INSTRUMENT))
                if amount <= 0:
                    continue
                ev =self._event(c, None, None, "sim_setup", "SIM_SETUP", "SERVICE", "ISSUE", "ACCEPTED",
                                 None, None, "SYNTHETIC_ISSUANCE", [], amount, {"account": acct})
                c.execute("INSERT OR IGNORE INTO accounts VALUES('issuer:bank_hk_h','bank_hk_h',?,0)",
                          (INSTRUMENT,))
                c.execute("UPDATE accounts SET balance_minor=balance_minor+? WHERE account_id=?", (amount, acct))
                c.execute("INSERT INTO postings(event_id,instrument,debit_account,credit_account,amount_minor,ts)"
                          " VALUES(?,?,?,?,?,?)", (ev, INSTRUMENT, "issuer:bank_hk_h", acct, amount, self.clock.iso()))
                total += amount
            prev = int(self._meta(c, "issued_supply") or 0)
            self._set_meta(c, "issued_supply", str(prev + total))

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _acct(owner: str) -> str:
        return f"{owner}:{INSTRUMENT}"

    @staticmethod
    def _escrow_acct(escrow_id: str) -> str:
        return f"escrow:{escrow_id}:{INSTRUMENT}"

    def _meta(self, c, key):
        r = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r["value"] if r else None

    def _set_meta(self, c, key, value):
        c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, value))

    def _next_seq(self, c) -> int:
        n = int(self._meta(c, "obj_seq") or 0) + 1
        self._set_meta(c, "obj_seq", str(n))
        return n

    def principal(self, principal_id: str) -> Principal:
        r = self.conn.execute("SELECT * FROM principals WHERE principal_id=?", (principal_id,)).fetchone()
        if not r:
            raise Rejection("UNKNOWN_PRINCIPAL", principal_id)
        return Principal(r["principal_id"], r["role"], r["entity_id"], r["display"] or "")

    def principals(self) -> list[Principal]:
        return [Principal(r["principal_id"], r["role"], r["entity_id"], r["display"] or "")
                for r in self.conn.execute("SELECT * FROM principals ORDER BY principal_id")]

    def _trade(self, c, trade_id) -> dict:
        r = c.execute("SELECT data FROM trades WHERE trade_id=?", (trade_id,)).fetchone()
        if not r:
            raise Rejection("UNKNOWN_TRADE", trade_id)
        return json.loads(r["data"])

    def _escrow(self, c, trade_id):
        return c.execute("SELECT * FROM escrows WHERE trade_id=?", (trade_id,)).fetchone()

    def _event(self, c, trade_id, escrow_id, actor_id, actor_role, actor_kind, operation, outcome,
               prior_state, new_state, reason_code, related, amount, details) -> str:
        last = c.execute("SELECT seq, hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq = (last["seq"] + 1) if last else 1
        prev = last["hash"] if last else GENESIS
        event_id = f"EVT-{seq:06d}"
        rec = {"event_id": event_id, "trade_id": trade_id, "escrow_id": escrow_id, "ts": self.clock.iso(),
               "actor_id": actor_id, "actor_role": actor_role, "actor_kind": actor_kind,
               "operation": operation, "outcome": outcome, "prior_state": prior_state,
               "new_state": new_state, "reason_code": reason_code,
               "related_attestation_ids": related or [], "amount_minor": amount,
               "details": details or {}, "prev_hash": prev}
        h = offchain.digest(rec)
        c.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (seq, event_id, trade_id, escrow_id, rec["ts"], actor_id, actor_role, actor_kind,
                   operation, outcome, prior_state, new_state, reason_code, _j(rec["related_attestation_ids"]),
                   amount, _j(rec["details"]), prev, h))
        return event_id

    def _set_state(self, c, esc, to_state: str) -> None:
        frm = esc["state"]
        if (frm, to_state) not in TRANSITIONS:
            raise IllegalTransition(f"{frm} -> {to_state}")
        n = c.execute("UPDATE escrows SET state=?, version=version+1, updated_at=? "
                      "WHERE escrow_id=? AND state=? AND version=?",
                      (to_state, self.clock.iso(), esc["escrow_id"], frm, esc["version"])).rowcount
        if n != 1:
            raise Rejection("CONCURRENT_STATE_CHANGE", "escrow changed concurrently")

    def _transfer(self, c, event_id, src, dst, amount):
        n = c.execute("UPDATE accounts SET balance_minor=balance_minor-? WHERE account_id=? AND balance_minor>=?",
                      (amount, src, amount)).rowcount
        if n != 1:
            raise Rejection("INSUFFICIENT_FUNDS", f"{src} cannot fund {amount}")
        c.execute("INSERT OR IGNORE INTO accounts VALUES(?,?,?,0)", (dst, dst.split(":")[0], INSTRUMENT))
        c.execute("UPDATE accounts SET balance_minor=balance_minor+? WHERE account_id=?", (amount, dst))
        c.execute("INSERT INTO postings(event_id,instrument,debit_account,credit_account,amount_minor,ts)"
                  " VALUES(?,?,?,?,?,?)", (event_id, INSTRUMENT, src, dst, amount, self.clock.iso()))

    def _attest(self, c, trade_id, type_, issuer: Principal, result, reason_code, *, checkpoint=None,
                subject_id=None, expires_at=None, input_digest=None, details=None, review_reference=None) -> str:
        seq = self._next_seq(c)
        att_id = f"ATT-{seq:05d}"
        rev = c.execute("SELECT COUNT(*) n FROM attestations WHERE trade_id=? AND type=?",
                        (trade_id, type_)).fetchone()["n"] + 1
        c.execute("INSERT INTO attestations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)",
                  (att_id, seq, trade_id, type_, checkpoint, subject_id, issuer.principal_id, issuer.role,
                   result, self.clock.iso(), expires_at, rev, input_digest, reason_code,
                   _j(details or {}), review_reference))
        return att_id

    def _current_docs(self, c, trade_id) -> tuple[dict, dict]:
        rows = c.execute("SELECT * FROM documents WHERE trade_id=? ORDER BY doc_type, revision", (trade_id,)).fetchall()
        latest: dict[str, Any] = {}
        for r in rows:          # highest revision wins (revision is a strict integer counter)
            latest[r["doc_type"]] = r
        docs = {k: json.loads(v["content"]) for k, v in latest.items()}
        meta = {k: {"doc_id": v["doc_id"], "revision": v["revision"], "digest": v["digest"]} for k, v in latest.items()}
        return docs, meta

    @staticmethod
    def _docs_digest(meta: dict) -> str:
        return offchain.digest({k: v["digest"] for k, v in sorted(meta.items())})

    def _active_holds(self, c, escrow_id):
        return c.execute("SELECT * FROM holds WHERE escrow_id=? AND status='ACTIVE'", (escrow_id,)).fetchall()

    def _latest_att(self, c, trade_id, type_, checkpoint=None, result=None):
        q = "SELECT * FROM attestations WHERE trade_id=? AND type=? AND revoked=0"
        a: list[Any] = [trade_id, type_]
        if checkpoint:
            q += " AND checkpoint=?"
            a.append(checkpoint)
        if result:
            q += " AND result=?"
            a.append(result)
        return c.execute(q + " ORDER BY seq DESC LIMIT 1", a).fetchone()

    # ---------------------------------------------------------- command shell
    def _execute(self, op: str, actor_id: str, trade_id: str | None,
                 fn: Callable[[Any, Principal], CommandResult], command_id: str | None = None) -> CommandResult:
        with transaction(self.conn) as c:
            if command_id:
                r = c.execute("SELECT result FROM commands WHERE command_id=?", (command_id,)).fetchone()
                if r:
                    res = CommandResult(**json.loads(r["result"]))
                    res.data = {**res.data, "idempotent_replay": True}
                    return res
            try:
                p = self.principal(actor_id)
            except Rejection:
                p = Principal(actor_id, "UNKNOWN", "UNKNOWN")
            esc = self._escrow(c, trade_id) if trade_id else None
            prior = esc["state"] if esc else None
            c.execute("SAVEPOINT cmd")
            try:
                if p.role not in PERMISSIONS[op]:
                    raise Rejection("RBAC_DENIED", f"role {p.role} may not perform {op}")
                res = fn(c, p)
                c.execute("RELEASE cmd")
            except Rejection as r:
                c.execute("ROLLBACK TO cmd")
                c.execute("RELEASE cmd")
                esc = self._escrow(c, trade_id) if trade_id else None
                ev = self._event(c, trade_id, esc["escrow_id"] if esc else None, p.principal_id, p.role, p.kind,
                                 op.upper(), "REJECTED", prior, prior, r.code, [], None,
                                 {"attempted": op, "message": r.message, **r.details})
                res = CommandResult(False, r.code, prior, ev, r.message, dict(r.details))
            if command_id:
                c.execute("INSERT INTO commands VALUES(?,?)", (command_id, _j(res.to_dict())))
            return res

    # ============================================================== COMMANDS
    def create_escrow(self, actor_id: str, trade: dict, contract: dict, command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            cfg = self.config
            if p.entity_id != trade.get("buyer_id"):
                raise Rejection("NOT_TRADE_BUYER", "only the trade's importer can fund its escrow")
            if c.execute("SELECT 1 FROM trades WHERE trade_id=?", (trade["trade_id"],)).fetchone():
                raise Rejection("DUPLICATE_TRADE", "an escrow already exists for this trade")
            for f in ("trade_id", "buyer_id", "seller_id", "issuer_bank_id", "recipient_bank_id", "currency",
                      "amount_minor", "invoice_id", "bill_of_lading_id", "shipment_id", "customs_declaration_id"):
                if trade.get(f) in (None, ""):
                    raise Rejection("INVALID_TERMS", f"missing {f}")
            if not isinstance(trade["amount_minor"], int) or trade["amount_minor"] <= 0:
                raise Rejection("INVALID_TERMS", "amount_minor must be a positive integer (cents)")
            if trade["currency"] != cfg["currency"]:
                raise Rejection("UNSUPPORTED_CURRENCY", "core prototype is single-currency synthetic HKD")
            if trade["issuer_bank_id"] != cfg["escrow_bank_id"]:
                raise Rejection("INVALID_TERMS", "escrow must be held at Bank H")
            if trade["amount_minor"] > cfg["txn_limit_minor"]:
                raise Rejection("TXN_LIMIT_EXCEEDED", f"limit {cfg['txn_limit_minor']} minor units",
                                {"limit_minor": cfg["txn_limit_minor"]})
            # creation checkpoint KYC/AML (simulated screening service)
            screen = self._screen(c, trade, "CREATION")
            if screen["result"] != "PASS":
                raise Rejection("CREATION_KYC_" + screen["result"], screen["reason_code"],
                                {"screening": screen})
            escrow_id = "ESC-" + trade["trade_id"].split("-", 1)[-1]
            now = self.clock.iso()
            c.execute("INSERT INTO trades VALUES(?,?,?)", (trade["trade_id"], _j({**trade, "escrow_id": escrow_id}), now))
            svc = self._svc(c, Role.SVC_COMPLIANCE)
            att = self._attest(c, trade["trade_id"], "KYC_AML", svc, "PASS", screen["reason_code"],
                               checkpoint="CREATION", subject_id=f"{trade['buyer_id']},{trade['seller_id']}",
                               details=screen)
            self._event(c, trade["trade_id"], escrow_id, svc.principal_id, svc.role, svc.kind, "ATTEST",
                        "ACCEPTED", None, None, "KYC_AML_CREATION_PASS", [att], None, {"checkpoint": "CREATION"})
            c.execute("INSERT INTO escrows VALUES(?,?,?,?,?,?,?)",
                      (escrow_id, trade["trade_id"], "__new__", 0, 0, now, now))
            # (None -> Created) is the only creation transition
            assert (None, State.CREATED) in TRANSITIONS
            c.execute("UPDATE escrows SET state=? WHERE escrow_id=?", (State.CREATED, escrow_id))
            ev_create = self._event(c, trade["trade_id"], escrow_id, p.principal_id, p.role, p.kind, "CREATE",
                                    "ACCEPTED", None, State.CREATED, "ESCROW_CREATED", [att], trade["amount_minor"],
                                    {"currency": trade["currency"]})
            ev_lock = self._event(c, trade["trade_id"], escrow_id, p.principal_id, p.role, p.kind, "LOCK",
                                  "ACCEPTED", State.CREATED, State.CREATED, "FUNDS_LOCKED", [],
                                  trade["amount_minor"], {"from": self._acct(trade["buyer_id"]),
                                                          "to": self._escrow_acct(escrow_id)})
            self._transfer(c, ev_lock, self._acct(trade["buyer_id"]), self._escrow_acct(escrow_id), trade["amount_minor"])
            c.execute("UPDATE escrows SET locked_minor=? WHERE escrow_id=?", (trade["amount_minor"], escrow_id))
            self._store_doc(c, trade["trade_id"], escrow_id, "CONTRACT", contract, p)
            return CommandResult(True, "ESCROW_CREATED", State.CREATED, ev_create,
                                 data={"escrow_id": escrow_id, "lock_event": ev_lock})
        return self._execute("create_escrow", actor_id, trade.get("trade_id"), fn, command_id)

    def _svc(self, c, role) -> Principal:
        r = c.execute("SELECT * FROM principals WHERE role=? ORDER BY principal_id LIMIT 1", (role,)).fetchone()
        return Principal(r["principal_id"], r["role"], r["entity_id"], r["display"] or "")

    def _screen(self, c, trade, checkpoint) -> dict:
        parties = {r["party_id"]: json.loads(r["data"]) for r in c.execute("SELECT * FROM parties")}
        wl = [dict(r) for r in c.execute("SELECT * FROM watchlist")]
        disp = {(r["party_id"], r["reason_code"]) for r in c.execute("SELECT * FROM dispositions")}
        res = offchain.screen_parties(parties, [trade["buyer_id"], trade["seller_id"]], trade, wl, disp, self.clock.iso())
        res["checkpoint"] = checkpoint
        return res

    def _store_doc(self, c, trade_id, escrow_id, doc_type, content, p: Principal) -> str:
        rev = c.execute("SELECT COALESCE(MAX(revision),0)+1 r FROM documents WHERE trade_id=? AND doc_type=?",
                        (trade_id, doc_type)).fetchone()["r"]
        doc_id = f"DOC-{trade_id}-{doc_type}-r{rev}"
        d = offchain.digest(content)
        c.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?)",
                  (doc_id, trade_id, doc_type, rev, p.principal_id, self.clock.iso(), _j(content), d))
        esc = self._escrow(c, trade_id)
        self._last_doc_event = self._event(c, trade_id, escrow_id, p.principal_id, p.role, p.kind, "SUBMIT_DOCUMENT", "ACCEPTED",
                    esc["state"], esc["state"], "DOCUMENT_REVISION_STORED", [], None,
                    {"doc_type": doc_type, "doc_id": doc_id, "revision": rev, "digest": d})
        # a new revision invalidates any DOCUMENTS approval tied to old content (invariant 7)
        stale = c.execute("SELECT attestation_id FROM attestations WHERE trade_id=? AND type='DOCUMENTS' "
                          "AND revoked=0", (trade_id,)).fetchall()
        if stale and rev > 1:
            ids = [s["attestation_id"] for s in stale]
            c.execute(f"UPDATE attestations SET revoked=1 WHERE attestation_id IN ({','.join('?'*len(ids))})", ids)
            self._event(c, trade_id, escrow_id, "engine", Role.SYSTEM_CONTRACT, "SERVICE", "REVOKE_ATTESTATION",
                        "ACCEPTED", esc["state"], esc["state"], "STALE_DOCUMENT_APPROVAL", ids, None,
                        {"superseded_by": doc_id})
        return doc_id

    def submit_document(self, actor_id: str, trade_id: str, doc_type: str, content: dict,
                        command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if esc["state"] in State.TERMINAL:
                raise Rejection("TERMINAL_STATE", esc["state"])
            if doc_type not in DOC_SUBMITTERS:
                raise Rejection("UNKNOWN_DOC_TYPE", doc_type)
            if p.role not in DOC_SUBMITTERS[doc_type]:
                raise Rejection("RBAC_DENIED", f"{p.role} may not submit {doc_type}")
            if p.role == Role.EXPORTER and p.entity_id != trade["seller_id"]:
                raise Rejection("NOT_TRADE_PARTY", "exporter is not the seller on this trade")
            if p.role == Role.IMPORTER and p.entity_id != trade["buyer_id"]:
                raise Rejection("NOT_TRADE_PARTY", "importer is not the buyer on this trade")
            doc_id = self._store_doc(c, trade_id, esc["escrow_id"], doc_type, content, p)
            return CommandResult(True, "DOCUMENT_STORED", esc["state"], self._last_doc_event, data={"doc_id": doc_id})
        return self._execute("submit_document", actor_id, trade_id, fn, command_id)

    def attest_shipment(self, actor_id: str, trade_id: str, shipment: dict,
                        command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if esc["state"] in State.TERMINAL:
                raise Rejection("TERMINAL_STATE", esc["state"])
            if shipment.get("trade_id", trade_id) != trade_id or shipment.get("shipment_id") != trade["shipment_id"]:
                raise Rejection("CROSS_TRADE_EVIDENCE", "shipment evidence does not belong to this trade",
                                {"expected_shipment_id": trade["shipment_id"],
                                 "received_shipment_id": shipment.get("shipment_id"),
                                 "received_trade_id": shipment.get("trade_id")})
            result = "PASS" if shipment.get("status") == "SHIPPED_ON_BOARD" else "FAIL"
            att = self._attest(c, trade_id, "SHIPMENT", p, result,
                               "SHIPPED_ON_BOARD" if result == "PASS" else "SHIPMENT_NOT_CONFIRMED",
                               subject_id=shipment["shipment_id"], input_digest=offchain.digest(shipment),
                               details=shipment)
            new = esc["state"]
            if result == "PASS" and esc["state"] == State.CREATED:
                self._set_state(c, esc, State.PENDING)
                new = State.PENDING
            ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "ATTEST", "ACCEPTED",
                             esc["state"], new, f"SHIPMENT_{result}", [att], None,
                             {"shipment_id": shipment["shipment_id"], "vessel": shipment.get("vessel")})
            return CommandResult(True, f"SHIPMENT_{result}", new, ev, data={"attestation_id": att})
        return self._execute("attest_shipment", actor_id, trade_id, fn, command_id)

    def run_document_check(self, actor_id: str, trade_id: str, command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if esc["state"] in State.TERMINAL:
                raise Rejection("TERMINAL_STATE", esc["state"])
            docs, meta = self._current_docs(c, trade_id)
            m = offchain.match_documents(trade, docs)
            att = self._attest(c, trade_id, "DOCUMENTS", p, m["result"], m["reason_code"],
                               subject_id=",".join(f"{k}@r{v['revision']}" for k, v in sorted(meta.items())),
                               input_digest=self._docs_digest(meta),
                               details={"findings": m["findings"], "revisions": meta})
            new = esc["state"]
            op = "ATTEST"
            if m["result"] == "FAIL" and esc["state"] in (State.CREATED, State.PENDING):
                self._set_state(c, esc, State.UNDER_REVIEW)
                new, op = State.UNDER_REVIEW, "REVIEW"
            ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, op, "ACCEPTED",
                             esc["state"], new, m["reason_code"], [att], None,
                             {"result": m["result"], "findings": m["findings"],
                              "assigned_reviewer_role": Role.BANK_HK if new == State.UNDER_REVIEW else None})
            return CommandResult(True, "DOCUMENTS_" + m["result"], new, ev,
                                 data={"attestation_id": att, "findings": m["findings"]})
        return self._execute("run_document_check", actor_id, trade_id, fn, command_id)

    def _freeze(self, c, esc, trade_id, p: Principal, reason, source, party_ids, related) -> tuple[str, str]:
        seq = self._next_seq(c)
        hold_id = f"HOLD-{seq:05d}"
        c.execute("INSERT INTO holds(hold_id,raised_seq,escrow_id,status,reason_code,party_ids,source,raised_by,raised_at)"
                  " VALUES(?,?,?,?,?,?,?,?,?)",
                  (hold_id, seq, esc["escrow_id"], "ACTIVE", reason, _j(party_ids), source, p.principal_id, self.clock.iso()))
        new = esc["state"]
        if esc["state"] != State.FROZEN:
            self._set_state(c, esc, State.FROZEN)
            new = State.FROZEN
        ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "FREEZE", "ACCEPTED",
                         esc["state"], new, reason, related, None,
                         {"hold_id": hold_id, "source": source, "party_ids": party_ids,
                          "denied_operations": ["settle", "refund", "resolve_review"]})
        return hold_id, ev

    def run_screening(self, actor_id: str, trade_id: str, checkpoint: str = "PRE_RELEASE",
                      command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if esc["state"] in State.TERMINAL:
                raise Rejection("TERMINAL_STATE", esc["state"])
            if checkpoint not in ("PRE_RELEASE", "ONGOING"):
                raise Rejection("INVALID_CHECKPOINT", checkpoint)
            s = self._screen(c, trade, checkpoint)
            exp = None
            if s["result"] == "PASS":
                exp = (self.clock.now() + timedelta(hours=self.config["prerelease_kyc_validity_hours"])).isoformat()
            att = self._attest(c, trade_id, "KYC_AML", p, s["result"], s["reason_code"], checkpoint=checkpoint,
                               subject_id=f"{trade['buyer_id']},{trade['seller_id']}", expires_at=exp, details=s)
            if s["result"] == "PASS":
                ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "ATTEST", "ACCEPTED",
                                 esc["state"], esc["state"], f"KYC_AML_{checkpoint}_PASS", [att], None,
                                 {"checkpoint": checkpoint, "expires_at": exp})
                return CommandResult(True, "SCREENING_PASS", esc["state"], ev, data={"attestation_id": att})
            parties = sorted({h["party_id"] for h in s["hits"]})
            hold_id, ev = self._freeze(c, esc, trade_id, p, s["reason_code"], "SCREENING_" + s["result"], parties, [att])
            return CommandResult(True, "SCREENING_" + s["result"], State.FROZEN, ev,
                                 data={"attestation_id": att, "hold_id": hold_id, "hits": s["hits"]})
        return self._execute("run_screening", actor_id, trade_id, fn, command_id)

    def raise_hold(self, actor_id: str, trade_id: str, reason_code: str = "MANUAL_COMPLIANCE_HOLD",
                   party_ids: list[str] | None = None, command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if esc["state"] in State.TERMINAL:
                raise Rejection("TERMINAL_STATE", esc["state"])
            hold_id, ev = self._freeze(c, esc, trade_id, p, reason_code, "MANUAL", party_ids or [], [])
            return CommandResult(True, "HOLD_RAISED", State.FROZEN, ev, data={"hold_id": hold_id})
        return self._execute("raise_hold", actor_id, trade_id, fn, command_id)

    def _post_review_state(self, c, trade_id) -> str:
        docs_att = self._latest_att(c, trade_id, "DOCUMENTS")
        if docs_att and docs_att["result"] == "FAIL":
            return State.UNDER_REVIEW
        trade = self._trade(c, trade_id)
        ship = self._latest_att(c, trade_id, "SHIPMENT")
        if ship and ship["result"] == "PASS" and ship["subject_id"] == trade["shipment_id"]:
            return State.PENDING
        return State.CREATED

    def resolve_hold(self, actor_id: str, trade_id: str, decision: str, review_reference: str,
                     note: str = "", command_id: str | None = None) -> CommandResult:
        """Authorised compliance review of a Frozen escrow.
        CLEAR     -> hold lifted as false positive; returns to Pending/Created/Under Review.
                     Never releases directly: a fresh pre-release screening is required.
        TERMINATE -> hold resolved with termination permitted; refund to importer."""
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if esc["state"] != State.FROZEN:
                raise Rejection("NOT_FROZEN", esc["state"])
            if not review_reference:
                raise Rejection("REVIEW_REFERENCE_REQUIRED", "a documented review reference is mandatory")
            holds = self._active_holds(c, esc["escrow_id"])
            if not holds:
                raise Rejection("NO_ACTIVE_HOLD", "")
            now = self.clock.iso()
            ids = [h["hold_id"] for h in holds]
            if decision == "CLEAR":
                for h in holds:
                    for pid in json.loads(h["party_ids"]):
                        c.execute("INSERT OR REPLACE INTO dispositions VALUES(?,?,?,?)",
                                  (pid, h["reason_code"], review_reference, now))
                c.execute(f"UPDATE holds SET status='CLEARED', resolved_by=?, resolved_at=?, decision='CLEAR', "
                          f"review_reference=? WHERE hold_id IN ({','.join('?'*len(ids))})",
                          (p.principal_id, now, review_reference, *ids))
                target = self._post_review_state(c, trade_id)
                self._set_state(c, esc, target)
                ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "REVIEW",
                                 "ACCEPTED", State.FROZEN, target, "HOLD_CLEARED_FALSE_POSITIVE", [], None,
                                 {"hold_ids": ids, "review_reference": review_reference, "note": note,
                                  "next_required": "fresh PRE_RELEASE screening before any release"})
                return CommandResult(True, "HOLD_CLEARED", target, ev)
            if decision == "TERMINATE":
                c.execute(f"UPDATE holds SET status='RESOLVED_TERMINATE', resolved_by=?, resolved_at=?, "
                          f"decision='TERMINATE', review_reference=? WHERE hold_id IN ({','.join('?'*len(ids))})",
                          (p.principal_id, now, review_reference, *ids))
                ev = self._refund(c, trade, esc, p, "COMPLIANCE_TERMINATION",
                                  {"hold_ids": ids, "review_reference": review_reference, "note": note})
                return CommandResult(True, "TERMINATED_REFUNDED", State.REFUNDED, ev)
            raise Rejection("INVALID_DECISION", decision)
        return self._execute("resolve_hold", actor_id, trade_id, fn, command_id)

    def _refund(self, c, trade, esc, p, reason, details) -> str:
        amount = esc["locked_minor"]
        self._set_state(c, esc, State.REFUNDED)
        ev = self._event(c, trade["trade_id"], esc["escrow_id"], p.principal_id, p.role, p.kind, "REFUND",
                         "ACCEPTED", esc["state"], State.REFUNDED, reason, [], amount,
                         {**details, "from": self._escrow_acct(esc["escrow_id"]), "to": self._acct(trade["buyer_id"])})
        self._transfer(c, ev, self._escrow_acct(esc["escrow_id"]), self._acct(trade["buyer_id"]), amount)
        c.execute("UPDATE escrows SET locked_minor=0 WHERE escrow_id=?", (esc["escrow_id"],))
        return ev

    def raise_dispute(self, actor_id: str, trade_id: str, reason: str, command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if p.role in (Role.IMPORTER, Role.EXPORTER) and p.entity_id not in (trade["buyer_id"], trade["seller_id"]):
                raise Rejection("NOT_TRADE_PARTY", "")
            if esc["state"] not in (State.CREATED, State.PENDING):
                raise Rejection("TERMINAL_STATE" if esc["state"] in State.TERMINAL else "INVALID_STATE", esc["state"])
            self._set_state(c, esc, State.UNDER_REVIEW)
            ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "REVIEW", "ACCEPTED",
                             esc["state"], State.UNDER_REVIEW, "MANUAL_DISPUTE", [], None,
                             {"reason": reason, "assigned_reviewer_role": Role.BANK_HK})
            return CommandResult(True, "DISPUTE_RAISED", State.UNDER_REVIEW, ev)
        return self._execute("raise_dispute", actor_id, trade_id, fn, command_id)

    def resolve_review(self, actor_id: str, trade_id: str, decision: str, review_reference: str,
                       note: str = "", command_id: str | None = None) -> CommandResult:
        """Authorised Bank H review of an Under Review escrow.
        REVALIDATE -> requires a current DOCUMENTS PASS on the latest revisions.
        TERMINATE  -> refund under the simulated dispute rule (blocked by any AML hold)."""
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if esc["state"] == State.FROZEN or self._active_holds(c, esc["escrow_id"]):
                raise Rejection("ACTIVE_HOLD", "AML/compliance hold must be resolved by compliance first")
            if esc["state"] in State.TERMINAL:
                raise Rejection("TERMINAL_STATE", esc["state"])
            if esc["state"] != State.UNDER_REVIEW:
                raise Rejection("NOT_UNDER_REVIEW", esc["state"])
            if not review_reference:
                raise Rejection("REVIEW_REFERENCE_REQUIRED", "")
            if decision == "REVALIDATE":
                _, meta = self._current_docs(c, trade_id)
                d = self._latest_att(c, trade_id, "DOCUMENTS")
                if not d or d["result"] != "PASS" or d["input_digest"] != self._docs_digest(meta):
                    raise Rejection("DOCUMENTS_NOT_REVALIDATED",
                                    "submit corrected documents and obtain a fresh document-check PASS first")
                ship = self._latest_att(c, trade_id, "SHIPMENT")
                target = State.PENDING if ship and ship["result"] == "PASS" else State.CREATED
                self._set_state(c, esc, target)
                ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "REVIEW",
                                 "ACCEPTED", State.UNDER_REVIEW, target, "REVIEW_REVALIDATED", [d["attestation_id"]],
                                 None, {"review_reference": review_reference, "note": note,
                                        "corrected_revisions": {k: v["revision"] for k, v in meta.items()}})
                return CommandResult(True, "REVIEW_REVALIDATED", target, ev)
            if decision == "TERMINATE":
                ev = self._refund(c, trade, esc, p, "DISPUTE_TERMINATION",
                                  {"review_reference": review_reference, "note": note})
                return CommandResult(True, "TERMINATED_REFUNDED", State.REFUNDED, ev)
            raise Rejection("INVALID_DECISION", decision)
        return self._execute("resolve_review", actor_id, trade_id, fn, command_id)

    # ------------------------------------------------------------ release
    def release_guard(self, trade_id: str, c=None) -> dict:
        """Evaluate the release guard without side effects. Returns every gate."""
        c = c or self.conn
        trade = self._trade(c, trade_id)
        esc = self._escrow(c, trade_id)
        now = self.clock.iso()
        gates: list[dict] = []

        def gate(name, ok, code, detail=""):
            gates.append({"gate": name, "ok": bool(ok), "code": "OK" if ok else code, "detail": detail})

        gate("escrow_ready", esc["state"] == State.PENDING and esc["locked_minor"] == trade["amount_minor"],
             {State.RELEASED: "TERMINAL_STATE", State.REFUNDED: "TERMINAL_STATE",
              State.FROZEN: "ESCROW_FROZEN", State.UNDER_REVIEW: "ESCROW_UNDER_REVIEW"}.get(
                 esc["state"], "ESCROW_NOT_READY"),
             f"state={esc['state']} locked={esc['locked_minor']}")
        holds = self._active_holds(c, esc["escrow_id"])
        gate("no_active_hold", not holds, "ACTIVE_HOLD", ",".join(h["hold_id"] for h in holds))
        ship = self._latest_att(c, trade_id, "SHIPMENT")
        gate("shipment_verified", ship and ship["result"] == "PASS" and ship["subject_id"] == trade["shipment_id"],
             "SHIPPING_NOT_VERIFIED", ship["attestation_id"] if ship else "missing")
        _, meta = self._current_docs(c, trade_id)
        d = self._latest_att(c, trade_id, "DOCUMENTS")
        gate("documents_verified", d and d["result"] == "PASS" and d["input_digest"] == self._docs_digest(meta),
             "DOCUMENTS_NOT_VERIFIED", d["attestation_id"] if d else "missing")
        k1 = self._latest_att(c, trade_id, "KYC_AML", "CREATION", "PASS")
        gate("kyc_creation_pass", k1, "CREATION_KYC_MISSING", k1["attestation_id"] if k1 else "missing")
        last_k = self._latest_att(c, trade_id, "KYC_AML")
        last_hold = c.execute("SELECT MAX(raised_seq) m FROM holds WHERE escrow_id=?", (esc["escrow_id"],)).fetchone()["m"] or 0
        k2 = last_k if (last_k and last_k["checkpoint"] == "PRE_RELEASE" and last_k["result"] == "PASS") else None
        fresh_order = bool(k2) and k2["seq"] > last_hold and (not d or k2["seq"] > d["seq"])
        gate("kyc_prerelease_pass", k2 and fresh_order, "PRE_RELEASE_KYC_MISSING",
             (k2["attestation_id"] if k2 else "missing") + ("" if fresh_order else " (absent or older than latest document approval/hold)"))
        gate("kyc_prerelease_current", k2 and k2["expires_at"] and k2["expires_at"] > now,
             "PRE_RELEASE_KYC_EXPIRED" if k2 else "PRE_RELEASE_KYC_MISSING", f"expires_at={k2['expires_at'] if k2 else None}")
        failed = [g for g in gates if not g["ok"]]
        return {"ok": not failed, "code": failed[0]["code"] if failed else "OK", "gates": gates,
                "evaluated_at": now,
                "attestations": [a for a in [ship and ship["attestation_id"], d and d["attestation_id"],
                                             k1 and k1["attestation_id"], k2 and k2["attestation_id"]] if a]}

    def settle(self, actor_id: str, trade_id: str, command_id: str | None = None) -> CommandResult:
        """The contract's release function: guard evaluation, one debit/credit
        posting and the RELEASE event commit atomically or not at all."""
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            g = self.release_guard(trade_id, c)
            if not g["ok"]:
                raise Rejection(g["code"], "release guard failed", {"guard": g})
            amount = esc["locked_minor"]
            msg = {"note": "ISO 20022-inspired mock fields (pacs.008-like); not schema-validated",
                   "MsgId": f"MOCK-{esc['escrow_id']}", "IntrBkSttlmAmt": {"Ccy": trade["currency"],
                                                                         "Amt": f"{amount/100:.2f}"},
                   "Dbtr": trade["buyer_id"], "DbtrAgt": trade["issuer_bank_id"],
                   "Cdtr": trade["seller_id"], "CdtrAgt": trade["recipient_bank_id"],
                   "RmtInf": trade["invoice_id"]}
            self._set_state(c, esc, State.RELEASED)
            ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "RELEASE", "ACCEPTED",
                             State.PENDING, State.RELEASED, "ALL_GATES_PASSED", g["attestations"], amount,
                             {"guard": g, "from": self._escrow_acct(esc["escrow_id"]),
                              "to": self._acct(trade["seller_id"]), "message": msg})
            self._transfer(c, ev, self._escrow_acct(esc["escrow_id"]), self._acct(trade["seller_id"]), amount)
            c.execute("UPDATE escrows SET locked_minor=0 WHERE escrow_id=?", (esc["escrow_id"],))
            return CommandResult(True, "RELEASED", State.RELEASED, ev, data={"amount_minor": amount})
        return self._execute("settle", actor_id, trade_id, fn, command_id)

    def acknowledge_receipt(self, actor_id: str, trade_id: str, command_id: str | None = None) -> CommandResult:
        def fn(c, p: Principal):
            trade = self._trade(c, trade_id)
            esc = self._escrow(c, trade_id)
            if p.entity_id != trade["recipient_bank_id"]:
                raise Rejection("NOT_TRADE_PARTY", "")
            if esc["state"] != State.RELEASED:
                raise Rejection("NOT_RELEASED", esc["state"])
            ev = self._event(c, trade_id, esc["escrow_id"], p.principal_id, p.role, p.kind, "ACKNOWLEDGE",
                             "ACCEPTED", State.RELEASED, State.RELEASED, "RECEIPT_OBSERVED_MOCK", [], None,
                             {"note": "Observation only; no real THB credit or cross-bank finality"})
            return CommandResult(True, "ACKNOWLEDGED", State.RELEASED, ev)
        return self._execute("acknowledge_receipt", actor_id, trade_id, fn, command_id)

    # ---------------------------------------------------- simulation controls
    def sim_add_watchlist(self, party_id: str, reason_code: str = "SANCTIONS_FLAG_SIMULATED") -> None:
        """Test/demo control: inject a synthetic watchlist entry (logged)."""
        with transaction(self.conn) as c:
            c.execute("INSERT INTO watchlist(party_id,reason_code,added_at,active) VALUES(?,?,?,1)",
                      (party_id, reason_code, self.clock.iso()))
            self._event(c, None, None, "sim_setup", "SIM_SETUP", "SERVICE", "SIM_WATCHLIST_ADD", "ACCEPTED",
                        None, None, reason_code, [], None, {"party_id": party_id})

    def sim_update_party(self, party_id: str, **fields) -> None:
        with transaction(self.conn) as c:
            r = c.execute("SELECT data FROM parties WHERE party_id=?", (party_id,)).fetchone()
            data = {**json.loads(r["data"]), **fields}
            c.execute("UPDATE parties SET data=? WHERE party_id=?", (_j(data), party_id))
            self._event(c, None, None, "sim_setup", "SIM_SETUP", "SERVICE", "SIM_PARTY_UPDATE", "ACCEPTED",
                        None, None, "SYNTHETIC_REGISTRY_CHANGE", [], None, {"party_id": party_id, "fields": list(fields)})

    # ================================================================= READS
    def escrow_state(self, trade_id: str) -> str | None:
        r = self._escrow(self.conn, trade_id)
        return r["state"] if r else None

    def escrow_row(self, trade_id: str) -> dict | None:
        r = self._escrow(self.conn, trade_id)
        return dict(r) if r else None

    def balance(self, owner: str) -> int:
        r = self.conn.execute("SELECT balance_minor FROM accounts WHERE account_id=?", (self._acct(owner),)).fetchone()
        return r["balance_minor"] if r else 0

    def escrow_balance(self, escrow_id: str) -> int:
        r = self.conn.execute("SELECT balance_minor FROM accounts WHERE account_id=?",
                              (self._escrow_acct(escrow_id),)).fetchone()
        return r["balance_minor"] if r else 0

    def accounts(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM accounts ORDER BY account_id")]

    def supply_check(self) -> dict:
        """Conservation invariant: sum of holder balances == issued supply, no negatives,
        and every escrow's locked amount equals its escrow account balance."""
        issued = int(self.conn.execute("SELECT value FROM meta WHERE key='issued_supply'").fetchone()["value"])
        rows = self.conn.execute("SELECT * FROM accounts WHERE account_id NOT LIKE 'issuer:%'").fetchall()
        total = sum(r["balance_minor"] for r in rows)
        negatives = [r["account_id"] for r in rows if r["balance_minor"] < 0]
        mismatched = []
        for e in self.conn.execute("SELECT * FROM escrows"):
            if self.escrow_balance(e["escrow_id"]) != e["locked_minor"]:
                mismatched.append(e["escrow_id"])
        # posting-level reconstruction
        recon: dict[str, int] = {}
        for p in self.conn.execute("SELECT * FROM postings"):
            recon[p["debit_account"]] = recon.get(p["debit_account"], 0) - p["amount_minor"]
            recon[p["credit_account"]] = recon.get(p["credit_account"], 0) + p["amount_minor"]
        recon_ok = all(recon.get(r["account_id"], 0) == r["balance_minor"] for r in rows)
        return {"ok": total == issued and not negatives and not mismatched and recon_ok,
                "issued_supply": issued, "holder_total": total, "negatives": negatives,
                "escrow_mismatches": mismatched, "postings_reconcile": recon_ok}

    def events(self, trade_id: str | None = None) -> list[dict]:
        q, a = "SELECT * FROM events", ()
        if trade_id:
            q, a = q + " WHERE trade_id=?", (trade_id,)
        out = []
        for r in self.conn.execute(q + " ORDER BY seq", a):
            d = dict(r)
            d["related_attestation_ids"] = json.loads(d["related_attestation_ids"])
            d["details"] = json.loads(d["details"])
            out.append(d)
        return out

    def attestations(self, trade_id: str) -> list[dict]:
        out = []
        for r in self.conn.execute("SELECT * FROM attestations WHERE trade_id=? ORDER BY seq", (trade_id,)):
            d = dict(r)
            d["details"] = json.loads(d["details"])
            out.append(d)
        return out

    def documents(self, trade_id: str) -> list[dict]:
        out = []
        for r in self.conn.execute("SELECT * FROM documents WHERE trade_id=? ORDER BY doc_type, revision", (trade_id,)):
            d = dict(r)
            d["content"] = json.loads(d["content"])
            out.append(d)
        return out

    def holds(self, trade_id: str) -> list[dict]:
        esc = self._escrow(self.conn, trade_id)
        if not esc:
            return []
        return [dict(r) for r in self.conn.execute("SELECT * FROM holds WHERE escrow_id=? ORDER BY raised_seq",
                                                   (esc["escrow_id"],))]

    def trade(self, trade_id: str) -> dict:
        return self._trade(self.conn, trade_id)

    def trade_ids(self) -> list[str]:
        return [r["trade_id"] for r in self.conn.execute("SELECT trade_id FROM trades ORDER BY trade_id")]

    def state_path(self, trade_id: str) -> list[str]:
        path = []
        for e in self.events(trade_id):
            if e["outcome"] == "ACCEPTED" and e["new_state"] and (not path or path[-1] != e["new_state"]):
                path.append(e["new_state"])
        return path

    def verify_journal(self) -> dict:
        """Recompute the hash chain. Detects any post-hoc modification, deletion or
        reordering of stored events (tamper-evident, not tamper-proof)."""
        prev = GENESIS
        for r in self.conn.execute("SELECT * FROM events ORDER BY seq"):
            rec = {"event_id": r["event_id"], "trade_id": r["trade_id"], "escrow_id": r["escrow_id"], "ts": r["ts"],
                   "actor_id": r["actor_id"], "actor_role": r["actor_role"], "actor_kind": r["actor_kind"],
                   "operation": r["operation"], "outcome": r["outcome"], "prior_state": r["prior_state"],
                   "new_state": r["new_state"], "reason_code": r["reason_code"],
                   "related_attestation_ids": json.loads(r["related_attestation_ids"]),
                   "amount_minor": r["amount_minor"], "details": json.loads(r["details"]), "prev_hash": r["prev_hash"]}
            if r["prev_hash"] != prev:
                return {"ok": False, "first_bad_event": r["event_id"], "problem": "BROKEN_LINK"}
            if offchain.digest(rec) != r["hash"]:
                return {"ok": False, "first_bad_event": r["event_id"], "problem": "CONTENT_HASH_MISMATCH"}
            prev = r["hash"]
        n = self.conn.execute("SELECT COUNT(*) n FROM events").fetchone()["n"]
        return {"ok": True, "events_checked": n, "head_hash": prev}
