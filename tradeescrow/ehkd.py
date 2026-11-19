"""CONCEPTUAL e-HKD interoperability extension (proposal Section 6.3).

Toy two-leg atomic settlement between
  Leg A  simulated tokenised COMMERCIAL-BANK deposits  (claims on Bank H / Bank O)
  Leg B  simulated CENTRAL-BANK money ("e-HKD-style" wholesale CeBM mock)
using a two-phase commit coordinator: both legs commit or neither does.

NOT IMPLEMENTED (by design): real e-HKD, HKMA systems, EnsembleTX, mBridge, legal
settlement finality, real multi-ledger atomicity, FX, or central-bank operation.
The two "ledgers" are Python objects in one process.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class LegFailure(Exception):
    pass


@dataclass
class MockLedger:
    name: str
    money_type: str                     # "commercial-bank money" | "central-bank money (conceptual)"
    balances: dict[str, int]
    reservations: dict[str, list[tuple[str, str, int]]] = field(default_factory=dict)
    fail_prepare: bool = False
    fail_commit_times: int = 0
    log: list[str] = field(default_factory=list)

    def supply(self) -> int:
        return sum(self.balances.values())

    def available(self, acct: str) -> int:
        held = sum(a for txs in self.reservations.values() for (s, _, a) in txs if s == acct)
        return self.balances.get(acct, 0) - held

    def prepare(self, tx_id: str, moves: list[tuple[str, str, int]]) -> None:
        if self.fail_prepare:
            self.log.append(f"{tx_id} PREPARE refused (injected fault)")
            raise LegFailure(f"{self.name}: prepare refused")
        need: dict[str, int] = {}
        for s, _, a in moves:
            need[s] = need.get(s, 0) + a
        for s, a in need.items():
            if self.available(s) < a:
                self.log.append(f"{tx_id} PREPARE refused: insufficient {s}")
                raise LegFailure(f"{self.name}: insufficient balance in {s}")
        self.reservations[tx_id] = moves
        self.log.append(f"{tx_id} PREPARED {moves}")

    def commit(self, tx_id: str) -> None:
        if self.fail_commit_times > 0:
            self.fail_commit_times -= 1
            self.log.append(f"{tx_id} COMMIT transient failure (injected), will retry")
            raise LegFailure(f"{self.name}: transient commit failure")
        for s, d, a in self.reservations.pop(tx_id):
            self.balances[s] -= a
            self.balances[d] = self.balances.get(d, 0) + a
        self.log.append(f"{tx_id} COMMITTED")

    def abort(self, tx_id: str) -> None:
        if self.reservations.pop(tx_id, None) is not None:
            self.log.append(f"{tx_id} ABORTED (reservation released)")


class AtomicSettlementCoordinator:
    """Two-phase commit: PREPARE all legs -> durable decision -> COMMIT all (with retry)
    or ABORT all. A crash before the decision is recovered by aborting."""

    def __init__(self, max_commit_retries: int = 3):
        self.decisions: dict[str, str] = {}
        self.max_commit_retries = max_commit_retries
        self.trace: list[str] = []

    def settle(self, tx_id: str, legs: list[tuple[MockLedger, list[tuple[str, str, int]]]],
               crash_before_decision: bool = False) -> dict:
        prepared: list[MockLedger] = []
        try:
            for ledger, moves in legs:
                ledger.prepare(tx_id, moves)
                prepared.append(ledger)
                self.trace.append(f"prepare {ledger.name}: ok")
        except LegFailure as e:
            self.trace.append(f"prepare failed: {e}; aborting all legs")
            for ledger in prepared:
                ledger.abort(tx_id)
            self.decisions[tx_id] = "ABORT"
            return {"tx_id": tx_id, "outcome": "ROLLED_BACK", "reason": str(e)}
        if crash_before_decision:
            self.trace.append("coordinator crash before decision (injected)")
            return self.recover(tx_id, [l for l, _ in legs])
        self.decisions[tx_id] = "COMMIT"          # durable decision point
        self.trace.append("decision COMMIT recorded")
        for ledger, _ in legs:
            for attempt in range(self.max_commit_retries + 1):
                try:
                    ledger.commit(tx_id)
                    self.trace.append(f"commit {ledger.name}: ok (attempt {attempt + 1})")
                    break
                except LegFailure:
                    self.trace.append(f"commit {ledger.name}: retry")
            else:
                return {"tx_id": tx_id, "outcome": "IN_DOUBT", "reason": "commit retries exhausted"}
        return {"tx_id": tx_id, "outcome": "COMMITTED_BOTH", "reason": ""}

    def recover(self, tx_id: str, ledgers: list[MockLedger]) -> dict:
        if self.decisions.get(tx_id) != "COMMIT":
            for l in ledgers:
                l.abort(tx_id)
            self.decisions[tx_id] = "ABORT"
            self.trace.append("recovery: no COMMIT decision found -> abort all")
            return {"tx_id": tx_id, "outcome": "ROLLED_BACK", "reason": "coordinator crash before decision"}
        return {"tx_id": tx_id, "outcome": "COMMIT_PENDING", "reason": ""}


CASES = {
    "success": "Both legs prepare and commit",
    "cebm_insufficient": "Bank H has insufficient central-bank money -> both legs roll back",
    "deposit_leg_refused": "Tokenised-deposit leg refuses prepare -> both roll back",
    "crash_before_decision": "Coordinator crashes after prepare, before decision -> recovery aborts both",
    "transient_commit": "CeBM commit fails once, retried under the durable COMMIT decision",
}


def run_case(case: str, amount_minor: int = 25_000_000) -> dict:
    """Interbank leg after an escrow release: the exporter's claim moves from Bank H to
    Bank O (leg A: commercial-bank money), and Bank H compensates Bank O in
    central-bank money (leg B)."""
    tdep = MockLedger("Tokenised-deposit ledger (commercial-bank money, simulated)", "commercial-bank money", {
        "exporter_th_01@BankH": amount_minor, "BankH:redemption": 0,
        "BankO:issuance": 1_000_000_000, "exporter_th_01@BankO": 0})
    cebm = MockLedger("e-HKD-style CeBM ledger (central-bank money, conceptual)", "central-bank money (conceptual)", {
        "BankH:CeBM": 10_000_000_000 if case != "cebm_insufficient" else amount_minor - 1,
        "BankO:CeBM": 5_000_000_000})
    if case == "deposit_leg_refused":
        tdep.fail_prepare = True
    if case == "transient_commit":
        cebm.fail_commit_times = 1
    before = {"A": dict(tdep.balances), "B": dict(cebm.balances)}
    supply_before = (tdep.supply(), cebm.supply())
    coord = AtomicSettlementCoordinator()
    legs = [
        (tdep, [("exporter_th_01@BankH", "BankH:redemption", amount_minor),
                ("BankO:issuance", "exporter_th_01@BankO", amount_minor)]),
        (cebm, [("BankH:CeBM", "BankO:CeBM", amount_minor)]),
    ]
    res = coord.settle(f"PVP-{case}", legs, crash_before_decision=(case == "crash_before_decision"))
    after = {"A": dict(tdep.balances), "B": dict(cebm.balances)}
    a_changed, b_changed = before["A"] != after["A"], before["B"] != after["B"]
    return {"case": case, "description": CASES[case], "result": res,
            "leg_a_changed": a_changed, "leg_b_changed": b_changed,
            "all_or_nothing_ok": a_changed == b_changed,
            "supply_conserved": (tdep.supply(), cebm.supply()) == supply_before,
            "no_reservations_left": not tdep.reservations and not cebm.reservations,
            "before": before, "after": after, "trace": coord.trace,
            "ledger_logs": {"A": tdep.log, "B": cebm.log},
            "disclaimer": "Conceptual illustration only; not a real e-HKD, HKMA, EnsembleTX or mBridge transaction."}
