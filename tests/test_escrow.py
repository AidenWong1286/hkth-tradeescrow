"""Executable test suite for HK-TH TradeEscrow (TC-001..TC-024 + supporting checks).

Every test drives the same EscrowService used by the UIs (no UI clicks).
Test IDs match requirements/test_cases.csv.
"""
from __future__ import annotations

import copy
import threading

import pytest

from tradeescrow.clock import SimClock
from tradeescrow.escrow import EscrowService
from tradeescrow.model import TRANSITIONS, AccessDenied, State
from tradeescrow.scenarios import (BANK, BANK_TH, COMPLIANCE, CONTRACT, CUSTOMS, EXPORTER, IMPORTER, LOGISTICS,
                                   REGULATOR, SVC_DOCS, SVC_KYC, Flow, load_fixture, new_service, scenario_tc001,
                                   scenario_tc002, scenario_tc003)
from tradeescrow.views import audit_export, redaction_probe, trade_view

TID = "TR-001"
AMT = 25_000_000


def snapshot(svc):
    return {"state": svc.escrow_state(TID), "accounts": svc.accounts()}


def release_postings(svc):
    return [e for e in svc.events(TID) if e["operation"] == "RELEASE" and e["outcome"] == "ACCEPTED"]


def refund_events(svc):
    return [e for e in svc.events(TID) if e["operation"] == "REFUND" and e["outcome"] == "ACCEPTED"]


def ready_to_release(svc=None) -> Flow:
    f = Flow(svc or new_service())
    f.up_to_docs()
    f.doc_check()
    f.prerelease()
    return f


# ---------------------------------------------------------------- flagship
def test_tc001_normal_settlement():
    f = scenario_tc001()
    s = f.svc
    assert s.state_path(TID) == [State.CREATED, State.PENDING, State.RELEASED]
    assert len(release_postings(s)) == 1
    assert s.balance("importer_hk_01") == 40_000_000 - AMT
    assert s.balance("exporter_th_01") == AMT
    assert s.escrow_balance("ESC-001") == 0
    assert s.supply_check()["ok"]
    assert s.verify_journal()["ok"]
    ops = [e["operation"] for e in s.events(TID) if e["outcome"] == "ACCEPTED"]
    for required in ("ATTEST", "CREATE", "LOCK", "SUBMIT_DOCUMENT", "RELEASE", "ACKNOWLEDGE"):
        assert required in ops
    rel = release_postings(s)[0]
    assert all(g["ok"] for g in rel["details"]["guard"]["gates"])


def test_tc002_document_mismatch_blocks_and_reviews():
    f = scenario_tc002(resolve=None)
    s = f.svc
    assert s.escrow_state(TID) == State.UNDER_REVIEW
    assert s.state_path(TID) == [State.CREATED, State.PENDING, State.UNDER_REVIEW]
    blocked = [st for st in f.steps if "must be blocked" in st["step"]][0]
    assert not blocked["ok"] and blocked["code"] == "ESCROW_UNDER_REVIEW"
    review = [e for e in s.events(TID) if e["operation"] == "REVIEW"][0]
    codes = {x["code"] for x in review["details"]["findings"]}
    assert "DOC_AMOUNT_MISMATCH" in codes
    assert s.balance("exporter_th_01") == 0 and s.escrow_balance("ESC-001") == AMT
    # mismatch is not an AML event
    assert not s.holds(TID)


def test_tc003_aml_alert_freezes():
    f = scenario_tc003(resolve=None)
    s = f.svc
    assert s.escrow_state(TID) == State.FROZEN
    assert [h["status"] for h in s.holds(TID)] == ["ACTIVE"]
    assert s.holds(TID)[0]["reason_code"] == "SANCTIONS_FLAG_SIMULATED"
    blocked = [st for st in f.steps if "must be blocked" in st["step"]]
    assert [b["ok"] for b in blocked] == [False, False]
    assert {b["code"] for b in blocked} == {"ESCROW_FROZEN", "ACTIVE_HOLD"}
    assert s.balance("exporter_th_01") == 0 and s.escrow_balance("ESC-001") == AMT
    # regulator sees the alert evidence read-only
    exp = audit_export(s, REGULATOR, TID)
    assert any(e["operation"] == "FREEZE" and e["reason_code"] == "SANCTIONS_FLAG_SIMULATED" for e in exp)


# ---------------------------------------------------------------- creation
def test_tc004_insufficient_funds():
    s = new_service()
    fx = load_fixture()
    before = s.accounts()
    t = dict(fx["trade"], amount_minor=50_000_000)       # importer holds 40,000,000
    c = dict(fx["contract"], amount_minor=50_000_000)
    r = s.create_escrow(IMPORTER, t, c)
    assert not r.ok and r.code == "INSUFFICIENT_FUNDS"
    assert s.escrow_state(TID) is None and s.accounts() == before
    assert s.events()[-1]["outcome"] == "REJECTED"


def test_tc004b_transaction_limit_and_currency():
    s = new_service()
    fx = load_fixture()
    r = s.create_escrow(IMPORTER, dict(fx["trade"], amount_minor=600_000_000), fx["contract"])
    assert r.code == "TXN_LIMIT_EXCEEDED"
    r = s.create_escrow(IMPORTER, dict(fx["trade"], currency="THB"), fx["contract"])
    assert r.code == "UNSUPPORTED_CURRENCY"
    assert s.escrow_state(TID) is None


def test_tc005_creation_kyc_fail():
    s = new_service()
    s.sim_update_party("exporter_th_01", kyc_status="UNVERIFIED")
    before = s.accounts()
    fx = load_fixture()
    r = s.create_escrow(IMPORTER, fx["trade"], fx["contract"])
    assert not r.ok and r.code == "CREATION_KYC_FAIL"
    assert s.escrow_state(TID) is None and s.accounts() == before


# ---------------------------------------------------------------- shipment
def test_tc006_missing_shipment_attestation():
    f = Flow(new_service())
    f.create(); f.customs(); f.exporter_docs(); f.doc_check(); f.prerelease()
    assert f.svc.escrow_state(TID) == State.CREATED
    r = f.svc.settle(CONTRACT, TID)
    assert not r.ok and r.code == "ESCROW_NOT_READY"
    gates = {g["gate"]: g["ok"] for g in r.data["guard"]["gates"]}
    assert gates["shipment_verified"] is False
    assert f.svc.balance("exporter_th_01") == 0


def test_tc007_cross_trade_shipment():
    f = Flow(new_service())
    f.create()
    bad = dict(f.fx["shipment_event"], trade_id="TR-002", shipment_id="SH-002")
    r = f.svc.attest_shipment(LOGISTICS, TID, bad)
    assert not r.ok and r.code == "CROSS_TRADE_EVIDENCE"
    assert f.svc.escrow_state(TID) == State.CREATED
    assert not [a for a in f.svc.attestations(TID) if a["type"] == "SHIPMENT"]


# ---------------------------------------------------------------- documents
def test_tc008_missing_customs_field():
    f = Flow(new_service())
    f.fx["customs_declaration"].pop("hs_code")
    f.up_to_docs()
    r = f.doc_check()
    assert r.code == "DOCUMENTS_FAIL"
    assert any(x.get("field") == "CUSTOMS_DECLARATION.hs_code" for x in r.data["findings"])
    assert f.svc.escrow_state(TID) == State.UNDER_REVIEW


def test_tc009_revision_invalidates_old_approval():
    f = ready_to_release()
    s = f.svc
    rev2 = dict(f.fx["bill_of_lading"], vessel="MV OTHER")
    assert s.submit_document(EXPORTER, TID, "BILL_OF_LADING", rev2).ok
    docs_atts = [a for a in s.attestations(TID) if a["type"] == "DOCUMENTS"]
    assert docs_atts and all(a["revoked"] == 1 for a in docs_atts)
    r = s.settle(CONTRACT, TID)
    assert not r.ok and r.code == "DOCUMENTS_NOT_VERIFIED"
    assert s.balance("exporter_th_01") == 0


# ---------------------------------------------------------------- compliance
def test_tc010_expired_prerelease_kyc():
    f = ready_to_release()
    s = f.svc
    s.clock.advance(hours=49)                       # validity window = 48h
    r = s.settle(CONTRACT, TID)
    assert not r.ok and r.code == "PRE_RELEASE_KYC_EXPIRED"
    assert s.balance("exporter_th_01") == 0
    assert s.run_screening(SVC_KYC, TID).ok          # new compliance decision
    assert s.settle(CONTRACT, TID).ok


def test_tc011_alert_after_pass_overrides():
    f = ready_to_release()
    s = f.svc
    r = s.raise_hold(COMPLIANCE, TID, "ADVERSE_MEDIA_SIMULATED", ["exporter_th_01"])
    assert r.ok and s.escrow_state(TID) == State.FROZEN
    r = s.settle(CONTRACT, TID)
    assert not r.ok and r.code == "ESCROW_FROZEN"
    gates = {g["gate"]: g["ok"] for g in r.data["guard"]["gates"]}
    assert gates["no_active_hold"] is False


def test_tc011b_ongoing_screening_alert_after_pass():
    f = ready_to_release()
    s = f.svc
    s.sim_add_watchlist("importer_hk_01", "PEP_MATCH_SIMULATED")
    r = s.run_screening(SVC_KYC, TID, "ONGOING")
    assert r.code == "SCREENING_ALERT" and s.escrow_state(TID) == State.FROZEN
    assert not s.settle(CONTRACT, TID).ok


# ---------------------------------------------------------------- idempotency
def test_tc012_duplicate_release():
    f = ready_to_release()
    s = f.svc
    r1 = s.settle(CONTRACT, TID, command_id="CMD-REL-1")
    r2 = s.settle(CONTRACT, TID, command_id="CMD-REL-1")    # same command replayed
    r3 = s.settle(BANK, TID, command_id="CMD-REL-2")        # new command, terminal state
    assert r1.ok and r2.ok and r2.data.get("idempotent_replay")
    assert not r3.ok and r3.code == "TERMINAL_STATE"
    assert len(release_postings(s)) == 1
    assert s.balance("exporter_th_01") == AMT and s.supply_check()["ok"]


def test_tc013_duplicate_refund():
    f = scenario_tc002(resolve=None)
    s = f.svc
    r1 = s.resolve_review(BANK, TID, "TERMINATE", "REV-1")
    r2 = s.resolve_review(BANK, TID, "TERMINATE", "REV-1")
    assert r1.ok and not r2.ok and r2.code == "TERMINAL_STATE"
    assert len(refund_events(s)) == 1
    assert s.balance("importer_hk_01") == 40_000_000 and s.supply_check()["ok"]


def test_tc014_refund_blocked_during_aml_hold():
    f = scenario_tc003(resolve=None)
    s = f.svc
    r = s.resolve_review(BANK, TID, "TERMINATE", "REV-9")
    assert not r.ok and r.code == "ACTIVE_HOLD"
    r = s.resolve_review(IMPORTER, TID, "TERMINATE", "REV-9")
    assert not r.ok and r.code == "RBAC_DENIED"
    assert s.escrow_state(TID) == State.FROZEN and s.escrow_balance("ESC-001") == AMT
    assert not refund_events(s)


# ---------------------------------------------------------------- RBAC / privacy
def test_tc015_exporter_cannot_approve_compliance():
    f = scenario_tc003(resolve=None)
    s = f.svc
    before = snapshot(s)
    for call in (lambda: s.resolve_hold(EXPORTER, TID, "CLEAR", "SELF"),
                 lambda: s.run_screening(EXPORTER, TID),
                 lambda: s.settle(EXPORTER, TID)):
        r = call()
        assert not r.ok and r.code == "RBAC_DENIED"
    assert snapshot(s) == before
    denied = [e for e in s.events(TID) if e["reason_code"] == "RBAC_DENIED"]
    assert len(denied) == 3 and all(e["actor_role"] == "EXPORTER" for e in denied)


def test_tc016_regulator_is_read_only():
    f = ready_to_release()
    s = f.svc
    before = snapshot(s)
    for call in (lambda: s.settle(REGULATOR, TID), lambda: s.raise_hold(REGULATOR, TID),
                 lambda: s.submit_document(REGULATOR, TID, "INVOICE", {}),
                 lambda: s.resolve_review(REGULATOR, TID, "TERMINATE", "R")):
        assert call().code == "RBAC_DENIED"
    assert snapshot(s) == before
    assert len(audit_export(s, REGULATOR, TID)) > 0


def test_tc017_no_cross_trade_disclosure():
    f = scenario_tc001()
    s = f.svc
    with pytest.raises(AccessDenied):
        trade_view(s, "u_importer_02", TID)
    with pytest.raises(AccessDenied):
        audit_export(s, "u_importer_02", TID)
    assert s.events()[-1]["operation"] == "READ" and s.events()[-1]["outcome"] == "REJECTED"
    assert trade_view(s, IMPORTER, TID)["state"] == State.RELEASED


# ---------------------------------------------------------------- integrity
def test_tc018_tamper_detection():
    f = scenario_tc001()
    s = f.svc
    assert s.verify_journal()["ok"]
    s.conn.execute("UPDATE events SET amount_minor=1 WHERE operation='RELEASE'")
    v = s.verify_journal()
    assert not v["ok"] and v["problem"] == "CONTENT_HASH_MISMATCH"


def test_tc018b_deletion_detection():
    f = scenario_tc001()
    s = f.svc
    s.conn.execute("DELETE FROM events WHERE seq=(SELECT seq FROM events WHERE operation='LOCK')")
    v = s.verify_journal()
    assert not v["ok"] and v["problem"] == "BROKEN_LINK"


def test_tc019_concurrent_release(tmp_path):
    db = str(tmp_path / "race.db")
    base = new_service(db)
    ready_to_release(base)
    now = base.clock.iso()
    workers = [EscrowService(db, SimClock(now)) for _ in range(8)]
    results = []
    barrier = threading.Barrier(len(workers))

    def go(i, w):
        barrier.wait()
        results.append(w.settle(CONTRACT, TID, command_id=f"RACE-{i}"))

    threads = [threading.Thread(target=go, args=(i, w)) for i, w in enumerate(workers)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    oks = [r for r in results if r.ok]
    assert len(results) == 8 and len(oks) == 1
    assert all(r.code == "TERMINAL_STATE" for r in results if not r.ok)
    check = EscrowService(db, SimClock(now))
    assert len(release_postings(check)) == 1
    assert check.balance("exporter_th_01") == AMT and check.supply_check()["ok"]
    assert check.verify_journal()["ok"]


def test_tc020_equal_time_revisions_deterministic():
    f = Flow(new_service())
    f.up_to_docs()
    s = f.svc
    a = dict(f.fx["invoice"], issue_date="2026-11-05")
    b = dict(f.fx["invoice"], issue_date="2026-11-06")
    s.submit_document(EXPORTER, TID, "INVOICE", a)     # revision 2, same simulated timestamp
    s.submit_document(EXPORTER, TID, "INVOICE", b)     # revision 3, same simulated timestamp
    invs = [d for d in s.documents(TID) if d["doc_type"] == "INVOICE"]
    assert [d["revision"] for d in invs] == [1, 2, 3]
    assert invs[1]["submitted_at"] == invs[2]["submitted_at"]
    r = f.doc_check()
    att = [x for x in s.attestations(TID) if x["type"] == "DOCUMENTS"][-1]
    assert "INVOICE@r3" in att["subject_id"] and r.code == "DOCUMENTS_PASS"


# ---------------------------------------------------------------- resolution paths
def test_tc021_cleared_dispute_requires_fresh_gates():
    f = Flow(new_service())
    f.fx["invoice"]["amount_minor"] = 24_500_000
    f.up_to_docs(); f.doc_check()
    s = f.svc
    assert s.escrow_state(TID) == State.UNDER_REVIEW
    f.prerelease()                                         # screening PASS while still under review
    assert not s.resolve_review(BANK, TID, "REVALIDATE", "REV-1").ok   # no corrected docs yet
    s.submit_document(EXPORTER, TID, "INVOICE", dict(f.fx["invoice"], amount_minor=AMT))
    f.doc_check()
    assert s.resolve_review(BANK, TID, "REVALIDATE", "REV-1").code == "REVIEW_REVALIDATED"
    r = s.settle(CONTRACT, TID)
    assert not r.ok and r.code == "PRE_RELEASE_KYC_MISSING"   # earlier screening is stale
    f.prerelease()
    assert f.settle().ok
    assert s.state_path(TID) == [State.CREATED, State.PENDING, State.UNDER_REVIEW, State.PENDING, State.RELEASED]


def test_tc022_authorised_termination_after_mismatch():
    f = scenario_tc002(resolve="TERMINATE")
    s = f.svc
    assert s.escrow_state(TID) == State.REFUNDED
    ev = refund_events(s)
    assert len(ev) == 1 and ev[0]["actor_role"] == "BANK_HK" and ev[0]["details"]["review_reference"]
    assert s.balance("importer_hk_01") == 40_000_000 and s.supply_check()["ok"]


def test_tc023_compliance_clearance_no_direct_release():
    f = scenario_tc003(resolve="CLEAR")
    s = f.svc
    cleared = [st for st in f.steps if st["code"] == "HOLD_CLEARED"][0]
    assert cleared["state"] == State.PENDING
    pre = [st for st in f.steps if "before fresh screening" in st["step"]][0]
    assert not pre["ok"] and pre["code"] == "PRE_RELEASE_KYC_MISSING"
    assert s.escrow_state(TID) == State.RELEASED
    assert s.state_path(TID) == [State.CREATED, State.PENDING, State.FROZEN, State.PENDING, State.RELEASED]


def test_tc023b_compliance_termination_refunds():
    f = scenario_tc003(resolve="TERMINATE")
    s = f.svc
    assert s.escrow_state(TID) == State.REFUNDED
    assert s.balance("importer_hk_01") == 40_000_000 and s.balance("exporter_th_01") == 0


def test_tc024_role_limited_audit_export():
    f = scenario_tc002(resolve="REVALIDATE")
    s = f.svc
    fx = load_fixture()
    commercial = [fx["contract"]["goods_description"], "unit_price_minor", "Harbour Kitchenware",
                  "u_importer_01", "u_exporter_01", "24500000"]
    reg = audit_export(s, REGULATOR, TID)
    assert redaction_probe(reg, commercial) == []
    assert all(set(e) <= {"event_id", "ts", "actor_role", "actor_kind", "operation", "outcome", "prior_state",
                          "new_state", "reason_code", "related_attestation_ids", "amount_minor", "prev_hash", "hash",
                          "details"} for e in reg)
    # regulator can still reconstruct the lifecycle from metadata alone
    path = []
    for e in reg:
        if e["outcome"] == "ACCEPTED" and e["new_state"] and (not path or path[-1] != e["new_state"]):
            path.append(e["new_state"])
    assert path == s.state_path(TID)
    bank_th = audit_export(s, BANK_TH, TID)
    assert redaction_probe(bank_th, commercial) == []
    with pytest.raises(AccessDenied):
        audit_export(s, LOGISTICS, TID)
    v = trade_view(s, LOGISTICS, TID)
    assert "amount_minor" not in v and "documents" in v and v["documents"] == []
    v = trade_view(s, REGULATOR, TID)
    assert "contract_terms" not in v and all("content" not in d for d in v["documents"])
    assert "documents" in trade_view(s, BANK, TID)


# ---------------------------------------------------------------- engine-wide invariants
@pytest.mark.parametrize("fn", [scenario_tc001, lambda: scenario_tc002(resolve="REVALIDATE"),
                                lambda: scenario_tc002(resolve="TERMINATE"),
                                lambda: scenario_tc003(resolve="CLEAR"),
                                lambda: scenario_tc003(resolve="TERMINATE")])
def test_only_declared_transitions(fn):
    s = fn().svc
    for e in s.events(TID):
        if e["outcome"] == "ACCEPTED" and e["prior_state"] != e["new_state"]:
            assert (e["prior_state"], e["new_state"]) in TRANSITIONS
    assert s.supply_check()["ok"] and s.verify_journal()["ok"]
    # never both released and refunded
    ops = {e["operation"] for e in s.events(TID) if e["outcome"] == "ACCEPTED"}
    assert not ({"RELEASE", "REFUND"} <= ops)


def test_rbac_non_buyer_cannot_create():
    s = new_service()
    fx = load_fixture()
    assert s.create_escrow(EXPORTER, fx["trade"], fx["contract"]).code == "RBAC_DENIED"
    assert s.create_escrow("u_importer_02", fx["trade"], fx["contract"]).code == "NOT_TRADE_BUYER"


def test_persistence_across_restart(tmp_path):
    db = str(tmp_path / "p.db")
    f = Flow(new_service(db))
    f.up_to_docs()
    again = EscrowService(db, SimClock(f.svc.clock.iso()))
    assert again.escrow_state(TID) == State.PENDING
    assert again.verify_journal()["ok"]


# ---------------------------------------------------------------- added after mutation analysis run 1
def test_tc007b_wrong_shipment_same_trade_id():
    """Added after mutation analysis: shipment evidence naming the right trade but the wrong shipment."""
    f = Flow(new_service())
    f.create()
    r = f.svc.attest_shipment(LOGISTICS, TID, dict(f.fx["shipment_event"], shipment_id="SH-999"))
    assert not r.ok and r.code == "CROSS_TRADE_EVIDENCE"
    assert f.svc.escrow_state(TID) == State.CREATED


def test_tc009b_digest_pin_is_independent_defence():
    """Added after mutation analysis: even if revocation were missed (simulated by un-revoking in the DB),
    the release guard still rejects an approval whose digest does not match the current documents."""
    f = ready_to_release()
    s = f.svc
    s.submit_document(EXPORTER, TID, "INVOICE", dict(f.fx["invoice"], issue_date="2026-11-06"))
    s.conn.execute("UPDATE attestations SET revoked=0 WHERE type='DOCUMENTS'")
    g = s.release_guard(TID)
    assert {x["gate"]: x["ok"] for x in g["gates"]}["documents_verified"] is False
    assert not s.settle(CONTRACT, TID).ok
