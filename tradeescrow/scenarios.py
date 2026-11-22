"""Reproducible scenario scripts (TC-001..TC-003 flagship + helpers).

Each script drives the *same* EscrowService used by the UIs, using fixed
synthetic fixtures and a deterministic simulated clock. Timestamps in these
logs are illustrative synthetic business times, not measurements.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from .clock import SimClock
from .escrow import EscrowService

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "base_fixture.json"

IMPORTER, EXPORTER = "u_importer_01", "u_exporter_01"
BANK, COMPLIANCE, BANK_TH = "u_bank_hk_ops", "u_bank_hk_compliance", "u_bank_th"
LOGISTICS, CUSTOMS, REGULATOR = "u_logistics", "u_customs", "u_regulator"
SVC_DOCS, SVC_KYC, CONTRACT = "svc_documents", "svc_compliance", "svc_contract"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def new_service(db_path: str = ":memory:", fixture: dict | None = None, config: dict | None = None) -> EscrowService:
    fx = fixture or load_fixture()
    svc = EscrowService(db_path, SimClock(), config)
    svc.setup(fx["principals"], fx["parties"], fx["issuance_minor"])
    return svc


class Flow:
    """Thin step recorder around the service, used by scenarios, tests and the UI auto-play."""

    def __init__(self, svc: EscrowService, fixture: dict | None = None):
        self.svc = svc
        self.fx = copy.deepcopy(fixture or load_fixture())
        self.steps: list[dict] = []

    @property
    def trade_id(self) -> str:
        return self.fx["trade"]["trade_id"]

    def _rec(self, label, actor, res):
        self.steps.append({"step": label, "actor": actor, "ok": res.ok, "code": res.code,
                           "state": self.svc.escrow_state(self.trade_id), "event_id": res.event_id,
                           "ts": self.svc.clock.iso()})
        return res

    # canonical steps -------------------------------------------------------
    def create(self, **kw):
        return self._rec("Importer funds escrow (creation KYC/AML + lock)", IMPORTER,
                         self.svc.create_escrow(IMPORTER, self.fx["trade"], self.fx["contract"], **kw))

    def customs(self):
        self.svc.clock.advance(days=2, hours=7)
        return self._rec("Customs submits export declaration", CUSTOMS,
                         self.svc.submit_document(CUSTOMS, self.trade_id, "CUSTOMS_DECLARATION",
                                                  self.fx["customs_declaration"]))

    def ship(self, shipment=None):
        self.svc.clock.advance(hours=18)
        return self._rec("Logistics attests shipped on board", LOGISTICS,
                         self.svc.attest_shipment(LOGISTICS, self.trade_id, shipment or self.fx["shipment_event"]))

    def exporter_docs(self):
        self.svc.clock.advance(hours=4)
        self._rec("Exporter submits commercial invoice", EXPORTER,
                  self.svc.submit_document(EXPORTER, self.trade_id, "INVOICE", self.fx["invoice"]))
        return self._rec("Exporter submits bill of lading", EXPORTER,
                         self.svc.submit_document(EXPORTER, self.trade_id, "BILL_OF_LADING", self.fx["bill_of_lading"]))

    def doc_check(self):
        self.svc.clock.advance(minutes=5)
        return self._rec("Document-matching service checks 4 documents", SVC_DOCS,
                         self.svc.run_document_check(SVC_DOCS, self.trade_id))

    def prerelease(self):
        self.svc.clock.advance(minutes=5)
        return self._rec("Pre-release KYC/AML screening", SVC_KYC,
                         self.svc.run_screening(SVC_KYC, self.trade_id, "PRE_RELEASE"))

    def settle(self, **kw):
        self.svc.clock.advance(minutes=1)
        return self._rec("Contract evaluates release guard", CONTRACT,
                         self.svc.settle(CONTRACT, self.trade_id, **kw))

    def ack(self):
        self.svc.clock.advance(minutes=10)
        return self._rec("Bank O acknowledges (observation only)", BANK_TH,
                         self.svc.acknowledge_receipt(BANK_TH, self.trade_id))

    def up_to_docs(self):
        self.create()
        self.customs()
        self.ship()
        self.exporter_docs()


# ---------------------------------------------------------------- scenarios
def scenario_tc001(svc: EscrowService | None = None) -> Flow:
    """Normal settlement: all attestations PASS -> Released."""
    f = Flow(svc or new_service())
    f.up_to_docs()
    f.doc_check()
    f.prerelease()
    f.settle()
    f.ack()
    return f


def scenario_tc002(svc: EscrowService | None = None, resolve: str | None = "REVALIDATE") -> Flow:
    """Document mismatch: invoice amount differs from contract -> Under Review.
    resolve=None stops at Under Review; REVALIDATE corrects and releases; TERMINATE refunds."""
    f = Flow(svc or new_service())
    f.fx["invoice"]["amount_minor"] = 24500000          # HKD 245,000.00 vs contracted 250,000.00
    f.up_to_docs()
    f.doc_check()
    f._rec("Release attempt while Under Review (must be blocked)", CONTRACT, f.svc.settle(CONTRACT, f.trade_id))
    if resolve is None:
        return f
    if resolve == "REVALIDATE":
        f.svc.clock.advance(hours=20)
        corrected = dict(f.fx["invoice"], amount_minor=25000000)
        f._rec("Exporter submits corrected invoice (revision 2)", EXPORTER,
               f.svc.submit_document(EXPORTER, f.trade_id, "INVOICE", corrected))
        f.doc_check()
        f.svc.clock.advance(hours=2)
        f._rec("Bank H reviewer revalidates", BANK,
               f.svc.resolve_review(BANK, f.trade_id, "REVALIDATE", "REV-DOC-0001", "invoice corrected to contract value"))
        f.prerelease()
        f.settle()
    else:
        f.svc.clock.advance(days=3)
        f._rec("Bank H terminates unresolved dispute", BANK,
               f.svc.resolve_review(BANK, f.trade_id, "TERMINATE", "REV-DOC-0002", "exporter did not correct"))
    return f


def scenario_tc003(svc: EscrowService | None = None, resolve: str | None = "CLEAR") -> Flow:
    """AML alert at pre-release screening -> Frozen.
    resolve=None stops at Frozen; CLEAR (false positive) -> Pending -> fresh screening -> Released;
    TERMINATE -> Refunded/Terminated."""
    f = Flow(svc or new_service())
    f.up_to_docs()
    f.doc_check()
    f.svc.sim_add_watchlist("exporter_th_01", "SANCTIONS_FLAG_SIMULATED")
    f.prerelease()
    f._rec("Release attempt while Frozen (must be blocked)", CONTRACT, f.svc.settle(CONTRACT, f.trade_id))
    f._rec("Refund attempt while hold unresolved (must be blocked)", BANK,
           f.svc.resolve_review(BANK, f.trade_id, "TERMINATE", "REV-X", "attempted refund"))
    if resolve is None:
        return f
    f.svc.clock.advance(days=1)
    if resolve == "CLEAR":
        f._rec("Compliance officer clears false positive", COMPLIANCE,
               f.svc.resolve_hold(COMPLIANCE, f.trade_id, "CLEAR", "AML-REV-0001", "name-match false positive"))
        f._rec("Release attempt before fresh screening (must be blocked)", CONTRACT, f.svc.settle(CONTRACT, f.trade_id))
        f.prerelease()
        f.settle()
    else:
        f._rec("Compliance confirms alert; termination permitted", COMPLIANCE,
               f.svc.resolve_hold(COMPLIANCE, f.trade_id, "TERMINATE", "AML-REV-0002", "true positive (simulated)"))
    return f


SCENARIOS = {
    "TC-001 Normal settlement": lambda svc=None: scenario_tc001(svc),
    "TC-002 Document mismatch -> review -> corrected -> released": lambda svc=None: scenario_tc002(svc, "REVALIDATE"),
    "TC-002b Document mismatch -> terminated/refunded": lambda svc=None: scenario_tc002(svc, "TERMINATE"),
    "TC-003 AML alert -> frozen -> cleared -> released": lambda svc=None: scenario_tc003(svc, "CLEAR"),
    "TC-003b AML alert -> frozen -> terminated/refunded": lambda svc=None: scenario_tc003(svc, "TERMINATE"),
}
