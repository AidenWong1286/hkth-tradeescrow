"""Core vocabulary: states, roles, permissions, transition table and results.

Everything here is *simulation* vocabulary for the HK-TH TradeEscrow teaching
prototype. No live bank, e-HKD, mBridge or blockchain is connected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# --------------------------------------------------------------------------
# Six escrow states (names fixed by the submitted proposal, Section 6.1)
# --------------------------------------------------------------------------
class State:
    CREATED = "Created"
    PENDING = "Pending"
    UNDER_REVIEW = "Under Review"
    FROZEN = "Frozen"
    RELEASED = "Released"
    REFUNDED = "Refunded/Terminated"

    ALL = (CREATED, PENDING, UNDER_REVIEW, FROZEN, RELEASED, REFUNDED)
    TERMINAL = (RELEASED, REFUNDED)


STATE_DEFINITIONS = {
    State.CREATED: "Simulated tokenised-deposit funds locked in escrow; escrow active.",
    State.PENDING: "Shipment confirmed by logistics attestation; remaining checks underway.",
    State.UNDER_REVIEW: "Document mismatch or other non-AML exception requires manual review.",
    State.FROZEN: "Compliance failure or AML alert; funds locked, no release or refund.",
    State.RELEASED: "All required attestations passed; funds moved to exporter.",
    State.REFUNDED: "Closed under the defined resolution logic; funds returned to importer.",
}

# Explicit allowed transitions (from, to) -> short trigger description.
# The engine refuses any transition not in this table (IllegalTransition).
TRANSITIONS: dict[tuple[str, str], str] = {
    (None, State.CREATED): "importer funds escrow; creation KYC/AML PASS; balance & limit OK",
    (State.CREATED, State.PENDING): "valid shipment attestation for this trade",
    (State.CREATED, State.UNDER_REVIEW): "document discrepancy / missing field / dispute",
    (State.PENDING, State.UNDER_REVIEW): "document discrepancy / missing field / dispute",
    (State.CREATED, State.FROZEN): "AML alert, compliance FAIL or explicit hold",
    (State.PENDING, State.FROZEN): "AML alert, compliance FAIL or explicit hold",
    (State.UNDER_REVIEW, State.FROZEN): "AML alert, compliance FAIL or explicit hold",
    (State.PENDING, State.RELEASED): "release guard: shipment+documents+2x KYC/AML current, no hold",
    (State.UNDER_REVIEW, State.PENDING): "authorised reviewer revalidates corrected documents",
    (State.UNDER_REVIEW, State.CREATED): "revalidated, but no shipment attestation yet",
    (State.UNDER_REVIEW, State.REFUNDED): "authorised termination of unresolved dispute (no AML hold)",
    (State.FROZEN, State.PENDING): "authorised compliance clearance; shipment verified",
    (State.FROZEN, State.CREATED): "authorised compliance clearance; no shipment yet",
    (State.FROZEN, State.UNDER_REVIEW): "authorised compliance clearance; documents still failing",
    (State.FROZEN, State.REFUNDED): "compliance decision permits termination and refund",
}


# --------------------------------------------------------------------------
# Roles: seven business participants + three simulated off-chain services
# --------------------------------------------------------------------------
class Role:
    IMPORTER = "IMPORTER"          # Hong Kong importer
    EXPORTER = "EXPORTER"          # Thai exporter
    BANK_HK = "BANK_HK"            # Hong Kong Bank H: escrow bank, control owner
    BANK_HK_COMPLIANCE = "BANK_HK_COMPLIANCE"  # Bank H compliance officer (part of Bank H)
    BANK_TH = "BANK_TH"            # Thai Bank O: receiving-bank observer
    LOGISTICS = "LOGISTICS"        # logistics provider
    CUSTOMS = "CUSTOMS"            # customs authority
    REGULATOR = "REGULATOR"        # read-only audit
    # simulated services (software modules, not real-world parties)
    SVC_DOCUMENTS = "SVC_DOCUMENTS"
    SVC_COMPLIANCE = "SVC_COMPLIANCE"
    SYSTEM_CONTRACT = "SYSTEM_CONTRACT"

    BUSINESS = (IMPORTER, EXPORTER, BANK_HK, BANK_HK_COMPLIANCE, BANK_TH, LOGISTICS, CUSTOMS, REGULATOR)
    SERVICES = (SVC_DOCUMENTS, SVC_COMPLIANCE, SYSTEM_CONTRACT)


ROLE_LABELS = {
    Role.IMPORTER: "Hong Kong importer",
    Role.EXPORTER: "Thai exporter",
    Role.BANK_HK: "Hong Kong Bank H (escrow operations)",
    Role.BANK_HK_COMPLIANCE: "Hong Kong Bank H (compliance officer)",
    Role.BANK_TH: "Thai Bank O (receiving-bank observer)",
    Role.LOGISTICS: "Logistics provider",
    Role.CUSTOMS: "Customs authority",
    Role.REGULATOR: "Regulator (read-only audit)",
    Role.SVC_DOCUMENTS: "Document-matching service (simulated)",
    Role.SVC_COMPLIANCE: "KYC/AML screening service (simulated)",
    Role.SYSTEM_CONTRACT: "Escrow contract engine (simulated)",
}

# Command -> roles allowed to issue it (server-side RBAC).
PERMISSIONS: dict[str, tuple[str, ...]] = {
    "create_escrow": (Role.IMPORTER,),
    "submit_document": (Role.EXPORTER, Role.IMPORTER, Role.CUSTOMS),
    "attest_shipment": (Role.LOGISTICS,),
    "run_document_check": (Role.SVC_DOCUMENTS, Role.BANK_HK),
    "run_screening": (Role.SVC_COMPLIANCE, Role.BANK_HK_COMPLIANCE),
    "raise_hold": (Role.BANK_HK_COMPLIANCE,),
    "resolve_hold": (Role.BANK_HK_COMPLIANCE,),
    "raise_dispute": (Role.IMPORTER, Role.EXPORTER, Role.BANK_HK),
    "resolve_review": (Role.BANK_HK,),
    "settle": (Role.SYSTEM_CONTRACT, Role.BANK_HK),
    "acknowledge_receipt": (Role.BANK_TH,),
}

# Document types each submitting role may submit.
DOC_SUBMITTERS = {
    "CONTRACT": (Role.IMPORTER,),
    "INVOICE": (Role.EXPORTER,),
    "BILL_OF_LADING": (Role.EXPORTER,),
    "CUSTOMS_DECLARATION": (Role.CUSTOMS,),
}

HUMAN_ROLES = set(Role.BUSINESS)


class Kind:
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


@dataclass
class Principal:
    principal_id: str
    role: str
    entity_id: str          # organisation the principal acts for
    display: str = ""

    @property
    def kind(self) -> str:
        return Kind.HUMAN if self.role in HUMAN_ROLES else Kind.SERVICE


@dataclass
class CommandResult:
    ok: bool
    code: str
    state: str | None = None
    event_id: str | None = None
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "code": self.code, "state": self.state,
                "event_id": self.event_id, "message": self.message, "data": self.data}


class Rejection(Exception):
    """A command was refused; the engine logs a REJECT event and changes nothing."""

    def __init__(self, code: str, message: str = "", details: dict | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details = details or {}


class IllegalTransition(Exception):
    """Programming-error guard: a state change outside TRANSITIONS was attempted."""


class AccessDenied(Exception):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
