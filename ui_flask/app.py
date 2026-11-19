"""HK-TH TradeEscrow — Flask demo console (verified build; offline fallback demo).

Run:  python -m ui_flask.app   ->  http://127.0.0.1:5050
Uses the same EscrowService as the Streamlit app and the pytest suite.

SCOPE / SECURITY NOTE: this is a single-operator, localhost classroom demo. The
"Act as" selector is role IMPERSONATION for demonstration, not authentication.
What it does guarantee: (1) every action runs as the selected principal and is
authorised by the engine; (2) every page that displays ledger data goes through
the role projections in tradeescrow.views (server-side), so a direct URL such as
/ledger cannot bypass them; (3) scenario/simulation controls (/sim/*) are
operator controls that are only served to loopback clients and can be switched
off entirely with TRADEESCROW_DEMO_CONTROLS=0.

UI LAYER (2026-11-19): pages are still fully server-rendered and work without
JavaScript. ui_flask/static/console.js only intercepts form posts, swaps the
re-rendered page in place and animates the difference between the previous and
the new page snapshot. The snapshot (#snap JSON) is built ONLY from data the
current role can already see on the page (role-projected view, role-filtered
audit events), so animation never reveals anything the projection hides.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from flask import Flask, Response, redirect, render_template, request, session, url_for

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tradeescrow import ehkd  # noqa: E402
from tradeescrow.model import ROLE_LABELS, STATE_DEFINITIONS, AccessDenied, Rejection, Role, State  # noqa: E402
from tradeescrow.scenarios import new_service  # noqa: E402
from tradeescrow.ui_actions import (ACTIONS, ROLE_ACTIONS, VARIANTS, autoplay_steps, fmt_hkd,  # noqa: E402
                                    run_action, run_autoplay, run_autoplay_step, variant_fixture)
from tradeescrow.views import VISIBILITY, audit_export, ledger_view, trade_view  # noqa: E402

app = Flask(__name__)
app.secret_key = os.environ.get("TRADEESCROW_SECRET") or os.urandom(24)   # per-process; demo only
TID = "TR-001"
STATE = {"svc": new_service(), "variant": "clean", "flash": None}
app.config["DEMO_CONTROLS"] = os.environ.get("TRADEESCROW_DEMO_CONTROLS", "1") != "0"
LOOPBACK = {"127.0.0.1", "::1", "localhost"}
SIM_CONTROLS = ("reset", "aml", "advance", "autoplay", "step", "tamper")

ROLE_ORDER = [Role.IMPORTER, Role.EXPORTER, Role.BANK_HK, Role.BANK_HK_COMPLIANCE, Role.BANK_TH,
              Role.LOGISTICS, Role.CUSTOMS, Role.REGULATOR]

# Short display names for the participant rail (labels only; authorisation is unchanged).
SHORT_ROLE = {Role.IMPORTER: "HK importer", Role.EXPORTER: "Thai exporter", Role.BANK_HK: "Bank H operations",
              Role.BANK_HK_COMPLIANCE: "Bank H compliance", Role.BANK_TH: "Bank O (Thailand)",
              Role.LOGISTICS: "Logistics", Role.CUSTOMS: "Customs", Role.REGULATOR: "Regulator"}

MONO_ROLE = {Role.IMPORTER: "IM", Role.EXPORTER: "EX", Role.BANK_HK: "BH", Role.BANK_HK_COMPLIANCE: "BC",
             Role.BANK_TH: "BO", Role.LOGISTICS: "LG", Role.CUSTOMS: "CU", Role.REGULATOR: "RG"}

GATE_LABELS = {
    "escrow_ready": "Escrow funded and ready",
    "no_active_hold": "No compliance hold",
    "shipment_verified": "Shipment verified on board",
    "documents_verified": "Documents match the contract",
    "kyc_creation_pass": "KYC/AML passed at creation",
    "kyc_prerelease_pass": "KYC/AML passed before release",
    "kyc_prerelease_current": "Screening still in date",
}

# Plain-English captions for result / reason codes (fallback: humanised code).
CODE_TEXT = {
    "ESCROW_CREATED": "Escrow created and HKD 250,000 locked",
    "DOCUMENT_STORED": "Document stored with its digest",
    "SHIPMENT_PASS": "Shipment attested on board",
    "DOCUMENTS_PASS": "Documents match the contract",
    "DOCUMENTS_FAIL": "Documents do not match: escrow sent to review",
    "SCREENING_PASS": "KYC/AML screening passed",
    "SCREENING_ALERT": "AML alert: escrow frozen",
    "RELEASED": "All 7 checks passed: funds released to the exporter",
    "ACKNOWLEDGED": "Bank O observed the receipt",
    "DISPUTE_RAISED": "Dispute raised: escrow under review",
    "REVIEW_REVALIDATED": "Reviewer revalidated the corrected documents",
    "HOLD_RAISED": "Compliance hold raised: escrow frozen",
    "HOLD_CLEARED": "Hold cleared as a false positive",
    "TERMINATED_REFUNDED": "Escrow terminated: importer refunded",
    "ESCROW_UNDER_REVIEW": "Release refused: escrow is under review",
    "ESCROW_FROZEN": "Release refused: escrow is frozen",
    "ESCROW_NOT_READY": "Release refused: escrow is not ready",
    "TERMINAL_STATE": "Refused: this escrow is already closed",
    "ACTIVE_HOLD": "Release refused: a compliance hold is active",
    "SHIPPING_NOT_VERIFIED": "Release refused: shipment not verified",
    "DOCUMENTS_NOT_VERIFIED": "Release refused: documents not verified",
    "PRE_RELEASE_KYC_MISSING": "Release refused: pre-release screening missing",
    "PRE_RELEASE_KYC_EXPIRED": "Release refused: screening has expired",
    "RBAC_DENIED": "Refused: this role is not allowed to do that",
    "NOT_TRADE_BUYER": "Refused: only this trade's importer can fund it",
    "NOT_TRADE_PARTY": "Refused: not a party to this trade",
    "ACTION_NOT_OFFERED": "Refused: that action is not offered to this role",
    "DUPLICATE_TRADE": "Refused: an escrow already exists for this trade",
    "RESET": "Fresh ledger loaded",
    "SIM_WATCHLIST_ADD": "Simulation: exporter added to a synthetic watchlist",
    "CLOCK": "Simulated clock moved forward",
    "AUTOPLAY": "Scenario replayed",
    "SIM_TAMPER": "Simulation: one stored journal event was edited",
}


def code_text(code: str) -> str:
    return CODE_TEXT.get(code) or code.replace("_", " ").capitalize()


def current_principal():
    svc = STATE["svc"]
    pid = session.get("principal", "u_importer_01")
    try:
        p = svc.principal(pid)
    except Rejection:
        p = None
    if p is None or p.role not in ROLE_ORDER:   # service identities cannot be impersonated from the UI
        session["principal"] = "u_importer_01"
        p = svc.principal("u_importer_01")
    return p


def demo_controls_allowed() -> bool:
    return bool(app.config["DEMO_CONTROLS"]) and (request.remote_addr or "") in LOOPBACK


@app.context_processor
def _inject():
    return {"demo_controls": demo_controls_allowed(), "short_role": SHORT_ROLE, "mono_role": MONO_ROLE}


@app.template_filter("hkd")
def _hkd(v):
    return fmt_hkd(v)


@app.template_filter("hkd0")
def _hkd0(v):
    return "—" if v is None else f"{v / 100:,.0f}"


def _corridor(svc, p, view) -> dict:
    """Amounts for the three vaults, limited to what this role may see.
    Bank H: all balances. Importer/exporter: own balance only. Others: none.
    The escrow amount is shown only to roles whose projection includes amounts."""
    fx = variant_fixture("clean")["trade"]
    buyer, seller = fx["buyer_id"], fx["seller_id"]
    scope = VISIBILITY.get(p.role, {}).get("balances", "none")
    imp = exp = None
    if scope == "all":
        imp, exp = svc.balance(buyer), svc.balance(seller)
    elif scope == "own":
        if p.entity_id == buyer:
            imp = svc.balance(buyer)
        elif p.entity_id == seller:
            exp = svc.balance(seller)
    locked = view.get("locked_minor") if view else None
    return {"importer": imp, "exporter": exp, "escrow": locked,
            "amount": view.get("amount_minor") if view else None}


def _guard_from_event(e: dict) -> list[dict] | None:
    d = e.get("details") or {}
    if "guard" in d:
        return [{"gate": g["gate"], "ok": g["ok"], "code": g.get("code", "")} for g in d["guard"]["gates"]]
    if "guard_gates" in d:   # metadata-only projection (regulator, Bank O)
        return [{"gate": g["gate"], "ok": g["ok"], "code": ""} for g in d["guard_gates"]]
    return None


def _snapshot(p, state, corridor, events, guard_event, journal, flash) -> dict:
    """Everything here is already rendered on the page for this role."""
    return {
        "viewer": p.principal_id, "role": p.role, "state": state,
        "corridor": corridor,
        "events": [{"id": e["event_id"], "op": e["operation"], "outcome": e["outcome"],
                    "prior": e.get("prior_state"), "new": e.get("new_state")} for e in events],
        "guard": guard_event,
        "journal_ok": journal["ok"],
        "flash": flash,
    }


@app.route("/")
def index():
    svc = STATE["svc"]
    p = current_principal()
    view, view_error, events, events_error = None, None, [], None
    exists = svc.escrow_state(TID) is not None
    if exists:
        try:
            view = trade_view(svc, p.principal_id, TID)
        except AccessDenied as e:
            view_error = e.code
        if VISIBILITY.get(p.role, {}).get("events", "none") == "none":
            events_error = "NO_AUDIT_ACCESS_FOR_ROLE"   # policy-level: not attempted, so nothing to log
        else:
            try:
                events = audit_export(svc, p.principal_id, TID)
            except AccessDenied as e:
                events_error = e.code
    principals = [x for x in svc.principals() if x.role in ROLE_ORDER]
    principals.sort(key=lambda x: (ROLE_ORDER.index(x.role), x.principal_id))
    actions = [(a, ACTIONS[a]) for a in ROLE_ACTIONS.get(p.role, [])]
    # The escrow state is part of the trade view: a participant whose trade_view was refused
    # (not a party to TR-001) must not learn it from the page either (fixed 2026-11-19).
    state = None if view_error else svc.escrow_state(TID)
    journal = svc.verify_journal()
    corridor = _corridor(svc, p, view)

    # Release guard: Bank H sees the live evaluation; other roles see the gates recorded in the
    # last release attempt they are allowed to read (full details or metadata-only guard_gates).
    guard_live = view.get("release_guard") if view else None
    guard_event = None
    for e in reversed(events):
        gates = _guard_from_event(e)
        if gates:
            guard_event = {"id": e["event_id"], "ok": e["outcome"] == "ACCEPTED", "reason": e["reason_code"],
                           "gates": gates}
            break

    # State path travelled, from visible accepted events.
    path = []
    for e in events:
        if e["outcome"] == "ACCEPTED" and e.get("new_state") and (not path or path[-1] != e["new_state"]):
            path.append(e["new_state"])
    if state and (not path or path[-1] != state):
        path.append(state)

    flash = STATE.pop("flash", None)
    if flash:
        flash = dict(flash, text=code_text(flash["code"]),
                     kind=("warn" if ("ALERT" in flash["code"] or "FAIL" in flash["code"]) else "good")
                     if flash["ok"] else "no")
    film = {v: [{"who": who, "action": a,
                 "role": SHORT_ROLE.get(svc.principal(who).role, who) if who != "sim" else "Simulation",
                 "label": ACTIONS[a][0] if a in ACTIONS else "Exporter appears on a synthetic watchlist",
                 "help": ACTIONS[a][2] if a in ACTIONS else "Operator control: synthetic sanctions flag"}
                for who, a in autoplay_steps(v)] for v in VARIANTS}
    snap = _snapshot(p, state, corridor, events, guard_event, journal, flash)
    return render_template("index.html", p=p, principals=principals, role_labels=ROLE_LABELS,
                           actions=actions, view=view, view_error=view_error, events=events,
                           events_error=events_error, state=state, states=State.ALL,
                           state_defs=STATE_DEFINITIONS, variant=STATE["variant"], variants=VARIANTS,
                           flash=flash, clock=svc.clock.iso(),
                           supply=svc.supply_check(), journal=journal, exists=exists,
                           escrow=svc.escrow_row(TID), corridor=corridor, guard_live=guard_live,
                           guard_event=guard_event, gate_labels=GATE_LABELS, path=path, film=film,
                           snap=snap, code_text=code_text, page="console")


@app.post("/as")
def switch():
    session["principal"] = request.form["principal"]
    return redirect(url_for("index"))


@app.post("/act/<action>")
def act(action):
    svc = STATE["svc"]
    p = current_principal()
    if action not in ROLE_ACTIONS.get(p.role, []):
        STATE["flash"] = {"ok": False, "code": "ACTION_NOT_OFFERED", "msg": "not offered to this role"}
        return redirect(url_for("index"))
    svc.clock.advance(minutes=30)   # each UI action = +30 simulated minutes (illustrative)
    try:
        r = run_action(svc, action, STATE["variant"], p.principal_id)
        STATE["flash"] = {"ok": r.ok, "code": r.code,
                          "msg": f"{ACTIONS[action][0]} as {p.principal_id} → {r.state} ({r.event_id})"}
    except Exception as e:  # unknown trade before creation etc.
        STATE["flash"] = {"ok": False, "code": type(e).__name__, "msg": str(e)}
    return redirect(url_for("index"))


def _tamper(svc) -> str | None:
    """Operator demo: edit one stored journal event in place (no re-hash), so the
    hash-chain verification visibly breaks. Reset the ledger to undo."""
    rows = svc.conn.execute("SELECT seq, event_id FROM events ORDER BY seq").fetchall()
    if len(rows) < 3:
        return None
    target = rows[len(rows) // 2]
    svc.conn.execute("UPDATE events SET reason_code = reason_code || '_EDITED' WHERE seq=?", (target["seq"],))
    svc.conn.commit()
    return target["event_id"]


@app.post("/sim/<what>")
def sim(what):
    if not demo_controls_allowed():
        return Response(json.dumps({"error": "DEMO_CONTROLS_DISABLED"}), status=403, mimetype="application/json")
    if what not in SIM_CONTROLS:
        return Response(json.dumps({"error": "UNKNOWN_SIM_CONTROL"}), status=404, mimetype="application/json")
    svc = STATE["svc"]
    if what == "reset":
        STATE["svc"] = new_service()
        STATE["variant"] = request.form.get("variant", STATE["variant"])
        STATE["flash"] = {"ok": True, "code": "RESET", "msg": f"Fresh ledger; scenario: {VARIANTS[STATE['variant']]}"}
    elif what == "aml":
        svc.sim_add_watchlist("exporter_th_01", "SANCTIONS_FLAG_SIMULATED")
        STATE["flash"] = {"ok": True, "code": "SIM_WATCHLIST_ADD", "msg": "Synthetic watchlist hit injected for exporter_th_01"}
    elif what == "advance":
        svc.clock.advance(hours=int(request.form.get("hours", 24)))
        STATE["flash"] = {"ok": True, "code": "CLOCK", "msg": f"Simulated clock now {svc.clock.iso()}"}
    elif what == "autoplay":
        variant = request.form.get("variant", STATE["variant"])
        STATE["svc"] = svc = new_service()
        STATE["variant"] = variant
        run_autoplay(svc, variant)
        STATE["flash"] = {"ok": True, "code": "AUTOPLAY", "msg": f"Replayed {VARIANTS[variant]} → {svc.escrow_state(TID)}"}
    elif what == "step":
        # Film mode: one autoplay step at a time, each run as its own principal (index 0 starts a fresh ledger).
        variant = request.form.get("variant", STATE["variant"])
        if variant not in VARIANTS:
            return Response(json.dumps({"error": "UNKNOWN_VARIANT"}), status=404, mimetype="application/json")
        i = int(request.form.get("i", 0))
        if i == 0:
            STATE["svc"] = svc = new_service()
            STATE["variant"] = variant
        who, action, r = run_autoplay_step(svc, variant, i)
        if r is None:
            STATE["flash"] = {"ok": True, "code": "SIM_WATCHLIST_ADD", "msg": "Synthetic watchlist hit injected"}
        else:
            STATE["flash"] = {"ok": r.ok, "code": r.code, "msg": f"{ACTIONS[action][0]} as {who} → {r.state}"}
    elif what == "tamper":
        ev = _tamper(svc)
        STATE["flash"] = {"ok": True, "code": "SIM_TAMPER",
                          "msg": f"Edited stored event {ev} without re-hashing" if ev else "Nothing to edit yet"}
    return redirect(request.referrer or url_for("index"))


@app.route("/intro")
def intro():
    """Opening page for demos and the video. Every figure is read from the code, not typed in."""
    from tradeescrow.model import TRANSITIONS
    facts = [(len(GATE_LABELS), "release checks, all required"), (len(ROLE_ORDER), "participant roles, each with its own view"),
             (len(TRANSITIONS), "permitted state transitions"), (len(VARIANTS), "scripted scenarios to replay")]
    return render_template("intro.html", p=current_principal(), role_labels=ROLE_LABELS, clock=STATE["svc"].clock.iso(),
                           facts=facts, page="intro")


@app.route("/ledger")
def ledger():
    svc = STATE["svc"]
    p = current_principal()
    try:
        lv = ledger_view(svc, p.principal_id)        # server-side role projection
    except AccessDenied as e:
        return render_template("ledger.html", lv=None, error=e.code, clock=svc.clock.iso(), p=p,
                               role_labels=ROLE_LABELS, page="ledger"), 403
    return render_template("ledger.html", lv=lv, error=None, clock=svc.clock.iso(), p=p, role_labels=ROLE_LABELS,
                           page="ledger")


@app.route("/ehkd", methods=["GET", "POST"])
def ehkd_page():
    case = request.form.get("case", "success")
    res = ehkd.run_case(case) if request.method == "POST" else None
    return render_template("ehkd.html", cases=ehkd.CASES, res=res, case=case, p=current_principal(),
                           role_labels=ROLE_LABELS, clock=STATE["svc"].clock.iso(), page="ehkd")


@app.route("/export.json")
def export():
    svc = STATE["svc"]
    p = current_principal()
    try:
        data = audit_export(svc, p.principal_id, TID)
    except AccessDenied as e:
        return Response(json.dumps({"error": e.code}), status=403, mimetype="application/json")
    return Response(json.dumps(data, indent=2, default=str), mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename=audit_{p.role}_{TID}.json"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5050)), debug=False)
