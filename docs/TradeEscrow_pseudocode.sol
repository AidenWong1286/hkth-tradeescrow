// SPDX-License-Identifier: UNLICENSED
// =====================================================================================
//  HK–TH TradeEscrow — Solidity-like PSEUDOCODE (proposal Section 5 / 6.1)
//  NOT compiled, NOT deployed, NOT audited. It documents the same rules that the
//  executable Python engine (tradeescrow/escrow.py) enforces and the tests verify.
//  The contract never observes the real world: shipment, document and KYC/AML facts
//  arrive as signed attestations from off-chain modules (oracles) that must be trusted.
// =====================================================================================
pragma solidity ^0.8.20;

interface ITokenisedDeposit {               // simulated Bank H tokenised HKD deposit (cents)
    function transferFrom(address from, address to, uint256 amountMinor) external returns (bool);
    function transfer(address to, uint256 amountMinor) external returns (bool);
}

contract TradeEscrow {
    enum State { None, Created, Pending, UnderReview, Frozen, Released, RefundedTerminated }
    enum Result { None, Pass, Fail, Alert }

    struct Attestation { Result result; uint64 issuedAt; uint64 expiresAt; bytes32 inputDigest; uint32 seq; bool revoked; }
    struct Trade {
        address importer; address exporter; uint256 amountMinor; bytes32 shipmentId;
        State state; uint32 version;
        Attestation shipment; Attestation documents; Attestation kycCreation; Attestation kycPreRelease;
        bytes32 currentDocsDigest;          // digest of latest revision of each document
        uint32 lastHoldSeq; uint8 activeHolds;
    }

    // ---- roles (permissioned network; assigned by Bank H governance) ----
    bytes32 constant IMPORTER = "IMPORTER";      bytes32 constant EXPORTER = "EXPORTER";
    bytes32 constant BANK_HK = "BANK_HK";        bytes32 constant BANK_HK_COMPLIANCE = "BANK_HK_COMPLIANCE";
    bytes32 constant LOGISTICS = "LOGISTICS";    bytes32 constant CUSTOMS = "CUSTOMS";
    bytes32 constant DOC_ORACLE = "SVC_DOCUMENTS"; bytes32 constant KYC_ORACLE = "SVC_COMPLIANCE";
    bytes32 constant REGULATOR = "REGULATOR";    // read-only: no state-changing function grants it
    mapping(address => bytes32) public roleOf;
    mapping(bytes32 => Trade) private trades;
    mapping(bytes32 => bool) private processedCommand;     // idempotency
    ITokenisedDeposit public immutable token;
    uint256 public constant TXN_LIMIT_MINOR = 500_000_000;  // HKD 5,000,000.00 (synthetic policy)
    uint64  public constant KYC_FRESHNESS = 48 hours;
    uint32  private seqCounter;

    event Transition(bytes32 indexed tradeId, State from, State to, bytes32 reason, address actor);
    event Rejected(bytes32 indexed tradeId, bytes32 operation, bytes32 reason, address actor);
    event AttestationRecorded(bytes32 indexed tradeId, bytes32 kind, Result result, bytes32 reason);

    modifier only(bytes32 role) { require(roleOf[msg.sender] == role, "RBAC_DENIED"); _; }
    modifier once(bytes32 commandId) { require(!processedCommand[commandId], "DUPLICATE_COMMAND"); processedCommand[commandId] = true; _; }

    constructor(ITokenisedDeposit t) { token = t; }

    function _move(Trade storage t, State to, bytes32 reason, bytes32 id) internal {
        require(_allowed(t.state, to), "ILLEGAL_TRANSITION");    // the 15-edge table, nothing else
        emit Transition(id, t.state, to, reason, msg.sender);
        t.state = to; t.version++;
    }

    function _allowed(State a, State b) internal pure returns (bool) {
        if (a == State.None) return b == State.Created;
        if (a == State.Created) return b == State.Pending || b == State.UnderReview || b == State.Frozen;
        if (a == State.Pending) return b == State.UnderReview || b == State.Frozen || b == State.Released;
        if (a == State.UnderReview) return b == State.Pending || b == State.Created || b == State.Frozen || b == State.RefundedTerminated;
        if (a == State.Frozen) return b == State.Pending || b == State.Created || b == State.UnderReview || b == State.RefundedTerminated;
        return false;                                            // Released / RefundedTerminated are terminal
    }

    // 1. Importer pre-funds: creation KYC/AML attestation must already be PASS
    function createEscrow(bytes32 id, address exporter, uint256 amountMinor, bytes32 shipmentId,
                          Attestation calldata kycCreation, bytes32 commandId) external only(IMPORTER) once(commandId) {
        Trade storage t = trades[id];
        require(t.state == State.None, "DUPLICATE_TRADE");
        require(amountMinor > 0 && amountMinor <= TXN_LIMIT_MINOR, "TXN_LIMIT_EXCEEDED");
        require(kycCreation.result == Result.Pass, "CREATION_KYC_FAIL");
        require(token.transferFrom(msg.sender, address(this), amountMinor), "INSUFFICIENT_FUNDS");  // LOCK
        t.importer = msg.sender; t.exporter = exporter; t.amountMinor = amountMinor; t.shipmentId = shipmentId;
        t.kycCreation = kycCreation;
        _move(t, State.Created, "ESCROW_CREATED", id);
    }

    // 2. Logistics oracle: shipment evidence must belong to THIS trade
    function attestShipment(bytes32 id, bytes32 shipmentId, Result r) external only(LOGISTICS) {
        Trade storage t = trades[id];
        require(t.state != State.Released && t.state != State.RefundedTerminated, "TERMINAL_STATE");
        require(shipmentId == t.shipmentId, "CROSS_TRADE_EVIDENCE");
        t.shipment = Attestation(r, uint64(block.timestamp), 0, shipmentId, ++seqCounter, false);
        if (r == Result.Pass && t.state == State.Created) _move(t, State.Pending, "SHIPMENT_PASS", id);
    }

    // 3. New document revision: digest changes and any prior approval is revoked
    function submitDocumentRevision(bytes32 id, bytes32 newDocsDigest) external {
        bytes32 r = roleOf[msg.sender];
        require(r == EXPORTER || r == CUSTOMS || r == IMPORTER, "RBAC_DENIED");
        Trade storage t = trades[id];
        t.currentDocsDigest = newDocsDigest;
        t.documents.revoked = true;                 // stale approval cannot be reused
    }

    // 4. Document-matching oracle (contract, invoice, B/L, customs declaration)
    function attestDocuments(bytes32 id, Result r, bytes32 inputDigest, bytes32 reason) external only(DOC_ORACLE) {
        Trade storage t = trades[id];
        t.documents = Attestation(r, uint64(block.timestamp), 0, inputDigest, ++seqCounter, false);
        if (r == Result.Fail && (t.state == State.Created || t.state == State.Pending))
            _move(t, State.UnderReview, reason, id);  // mismatch -> manual review, never auto-release
    }

    // 5. KYC/AML oracle: PASS is valid for 48h; ALERT/FAIL freezes and opens a hold
    function attestScreening(bytes32 id, Result r, bytes32 reason) external only(KYC_ORACLE) {
        Trade storage t = trades[id];
        uint32 s = ++seqCounter;
        if (r == Result.Pass) {
            t.kycPreRelease = Attestation(r, uint64(block.timestamp), uint64(block.timestamp) + KYC_FRESHNESS, 0, s, false);
        } else {
            t.activeHolds++; t.lastHoldSeq = s;
            if (t.state != State.Frozen) _move(t, State.Frozen, reason, id);
        }
    }

    // 6. THE RELEASE GUARD — all conditions current, atomically with the transfer
    function settle(bytes32 id, bytes32 commandId) external once(commandId) {
        require(roleOf[msg.sender] == BANK_HK || msg.sender == address(this), "RBAC_DENIED");
        Trade storage t = trades[id];
        require(t.state == State.Pending, "ESCROW_NOT_READY");
        require(t.activeHolds == 0, "ACTIVE_HOLD");
        require(t.shipment.result == Result.Pass, "SHIPPING_NOT_VERIFIED");
        require(t.documents.result == Result.Pass && !t.documents.revoked
                && t.documents.inputDigest == t.currentDocsDigest, "DOCUMENTS_NOT_VERIFIED");
        require(t.kycCreation.result == Result.Pass, "CREATION_KYC_MISSING");
        require(t.kycPreRelease.result == Result.Pass && t.kycPreRelease.seq > t.lastHoldSeq
                && t.kycPreRelease.seq > t.documents.seq, "PRE_RELEASE_KYC_MISSING");
        require(block.timestamp < t.kycPreRelease.expiresAt, "PRE_RELEASE_KYC_EXPIRED");
        _move(t, State.Released, "ALL_GATES_PASSED", id);       // effects before interaction
        require(token.transfer(t.exporter, t.amountMinor), "TRANSFER_FAILED");
    }

    // 7. Exception resolution — human review is explicit and logged, never self-certified
    function resolveReview(bytes32 id, bool revalidate, bytes32 reviewRef) external only(BANK_HK) {
        Trade storage t = trades[id];
        require(t.activeHolds == 0, "ACTIVE_HOLD");
        require(t.state == State.UnderReview, "NOT_UNDER_REVIEW");
        require(reviewRef != 0, "REVIEW_REFERENCE_REQUIRED");
        if (revalidate) {
            require(t.documents.result == Result.Pass && t.documents.inputDigest == t.currentDocsDigest, "DOCUMENTS_NOT_REVALIDATED");
            _move(t, t.shipment.result == Result.Pass ? State.Pending : State.Created, "REVIEW_REVALIDATED", id);
        } else {
            _move(t, State.RefundedTerminated, "DISPUTE_TERMINATION", id);
            require(token.transfer(t.importer, t.amountMinor), "TRANSFER_FAILED");
        }
    }

    function resolveHold(bytes32 id, bool clearFalsePositive, bytes32 reviewRef) external only(BANK_HK_COMPLIANCE) {
        Trade storage t = trades[id];
        require(t.state == State.Frozen && t.activeHolds > 0, "NOT_FROZEN");
        require(reviewRef != 0, "REVIEW_REFERENCE_REQUIRED");
        t.activeHolds = 0;
        if (clearFalsePositive) {
            // returns to the prior stage; a FRESH pre-release screening is still required before settle()
            State back = t.documents.result == Result.Fail ? State.UnderReview
                       : (t.shipment.result == Result.Pass ? State.Pending : State.Created);
            _move(t, back, "HOLD_CLEARED_FALSE_POSITIVE", id);
        } else {
            _move(t, State.RefundedTerminated, "COMPLIANCE_TERMINATION", id);
            require(token.transfer(t.importer, t.amountMinor), "TRANSFER_FAILED");
        }
    }
}
