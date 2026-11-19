"""HK-TH TradeEscrow — Streamlit interactive prototype (proposal Section 5).

Run:  pip install -r requirements.txt  &&  streamlit run ui_streamlit/streamlit_app.py
Uses the same EscrowService, action catalogue and role projections as the
Flask console and the pytest suite. All data are synthetic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tradeescrow import ehkd  # noqa: E402
from tradeescrow.model import ROLE_LABELS, STATE_DEFINITIONS, AccessDenied, Role, State  # noqa: E402
from tradeescrow.scenarios import new_service  # noqa: E402
from tradeescrow.ui_actions import ACTIONS, ROLE_ACTIONS, VARIANTS, fmt_hkd, run_action, run_autoplay  # noqa: E402
from tradeescrow.views import VISIBILITY, audit_export, ledger_view, trade_view  # noqa: E402

TID = "TR-001"
STATE_COLORS = {State.CREATED: "#64748b", State.PENDING: "#b7791f", State.UNDER_REVIEW: "#c2410c",
                State.FROZEN: "#1d4ed8", State.RELEASED: "#15803d", State.REFUNDED: "#7c3aed"}
ROLE_ORDER = [Role.IMPORTER, Role.EXPORTER, Role.BANK_HK, Role.BANK_HK_COMPLIANCE, Role.BANK_TH,
              Role.LOGISTICS, Role.CUSTOMS, Role.REGULATOR]

st.set_page_config(page_title="HK–TH TradeEscrow", layout="wide")

if "svc" not in st.session_state:
    st.session_state.svc = new_service()
    st.session_state.variant = "clean"
    st.session_state.last = None
svc = st.session_state.svc

st.title("HK–TH TradeEscrow")
st.caption("Tokenised-deposit escrow prototype for Hong Kong–Thailand trade finance · FTEC3002 Group 1")
st.warning("SIMULATION — synthetic data only. Tokenised deposits, attestations, KYC/AML results and the e-HKD "
           "leg are mocks; no bank, HKMA, e-HKD, EnsembleTX or mBridge system is connected.")

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Demo controls")
    principals = sorted([p for p in svc.principals() if p.role in ROLE_ORDER],
                        key=lambda p: (ROLE_ORDER.index(p.role), p.principal_id))
    labels = {p.principal_id: f"{ROLE_LABELS[p.role]} — {p.principal_id}" for p in principals}
    pid = st.selectbox("Act as participant", list(labels), format_func=labels.get)
    me = svc.principal(pid)
    st.caption("Role impersonation for a single-operator demo — not authentication. "
               "Actions run as the selected participant; the engine authorises them.")
    st.markdown("**Operator simulation controls**")
    variant = st.selectbox("Scenario fixture", list(VARIANTS), format_func=VARIANTS.get,
                           index=list(VARIANTS).index(st.session_state.variant))
    c1, c2 = st.columns(2)
    if c1.button("Reset ledger"):
        st.session_state.svc = svc = new_service()
        st.session_state.variant = variant
        st.session_state.last = ("RESET", True, VARIANTS[variant])
        st.rerun()
    if c2.button("▶ Auto-play"):
        st.session_state.svc = svc = new_service()
        st.session_state.variant = variant
        run_autoplay(svc, variant)
        st.session_state.last = ("AUTOPLAY", True, f"{VARIANTS[variant]} → {svc.escrow_state(TID)}")
        st.rerun()
    c3, c4 = st.columns(2)
    if c3.button("Inject AML hit"):
        svc.sim_add_watchlist("exporter_th_01", "SANCTIONS_FLAG_SIMULATED")
        st.session_state.last = ("SIM_WATCHLIST_ADD", True, "synthetic watchlist hit for exporter_th_01")
    if c4.button("Clock +24h"):
        svc.clock.advance(hours=24)
    st.caption(f"Simulated clock: {svc.clock.iso()[:16].replace('T', ' ')} HKT")

    st.subheader(f"Actions — {ROLE_LABELS[me.role]}")
    for a in ROLE_ACTIONS.get(me.role, []):
        label, _, help_ = ACTIONS[a]
        if st.button(label, key=f"act_{a}", help=help_ or None, use_container_width=True):
            svc.clock.advance(minutes=30)
            try:
                r = run_action(svc, a, st.session_state.variant, me.principal_id)
                st.session_state.last = (r.code, r.ok, f"{label} as {me.principal_id} → {r.state} ({r.event_id})")
            except Exception as e:  # e.g. acting before the escrow exists
                st.session_state.last = (type(e).__name__, False, str(e))
            st.rerun()

if st.session_state.last:
    code, ok, msg = st.session_state.last
    (st.success if ok and "ALERT" not in code and "FAIL" not in code else st.error if not ok else st.warning)(
        f"**{code}** — {msg}")

tab_escrow, tab_audit, tab_ledger, tab_ehkd, tab_about = st.tabs(
    ["Escrow", "Audit trail", "Ledger & integrity", "e-HKD concept", "About / scope"])

state = svc.escrow_state(TID)
with tab_escrow:
    cols = st.columns(6)
    for i, s in enumerate(State.ALL):
        on = s == state
        cols[i].markdown(
            f"<div style='text-align:center;padding:6px;border-radius:999px;font-size:13px;"
            f"background:{STATE_COLORS[s] if on else '#f1f5f9'};color:{'#fff' if on else '#64748b'};"
            f"font-weight:{700 if on else 400}'>{s}</div>", unsafe_allow_html=True)
    st.write(f"**{state}** — {STATE_DEFINITIONS[state]}" if state else
             "No escrow yet — act as the Hong Kong importer and create & fund it.")
    sc, jv = svc.supply_check(), svc.verify_journal()
    m1, m2, m3 = st.columns(3)
    sees_amount = "amount" in VISIBILITY.get(me.role, {}).get("groups", [])
    m1.metric("Locked in escrow", fmt_hkd(svc.escrow_row(TID)["locked_minor"]) if state and sees_amount
              else ("—" if not state else "not visible to role"))
    m2.metric("Ledger conservation", "OK" if sc["ok"] else "FAIL")
    m3.metric("Journal hash chain", "intact" if jv["ok"] else "BROKEN")
    if state:
        left, right = st.columns([3, 2])
        with left:
            st.subheader(f"What {ROLE_LABELS[me.role]} can see")
            try:
                v = trade_view(svc, pid, TID)
                base = {k: v[k] for k in v if not isinstance(v[k], (list, dict))}
                st.table(pd.DataFrame({"field": list(base), "value": [
                    fmt_hkd(x) if k.endswith("_minor") else x for k, x in base.items()]}))
                if v.get("attestations"):
                    st.markdown("**Attestations**")
                    st.dataframe(pd.DataFrame(v["attestations"]).drop(columns=["details"], errors="ignore"),
                                 use_container_width=True, hide_index=True)
                if v.get("documents"):
                    st.markdown("**Documents**")
                    st.dataframe(pd.DataFrame([{k: d.get(k) for k in ("doc_type", "revision", "digest")}
                                               for d in v["documents"]]), use_container_width=True, hide_index=True)
            except AccessDenied as e:
                st.error(f"{e.code}: this role has no access to {TID} (denial logged).")
                v = {}
        with right:
            if v.get("release_guard"):
                st.subheader("Release guard (live)")
                for g in v["release_guard"]["gates"]:
                    st.write(("✅ " if g["ok"] else "❌ ") + g["gate"].replace("_", " ") +
                             ("" if g["ok"] else f" — `{g['code']}`"))
                if state in State.TERMINAL:
                    st.info(f"Escrow closed ({state}).")
                elif v["release_guard"]["ok"]:
                    st.success("Release permitted")
                else:
                    st.error(f"Release blocked: {v['release_guard']['code']}")
            if v.get("holds"):
                st.subheader("Compliance holds")
                st.dataframe(pd.DataFrame(v["holds"]), hide_index=True)

with tab_audit:
    if not state:
        st.info("No events for TR-001 yet.")
    elif VISIBILITY.get(me.role, {}).get("events", "none") == "none":
        st.error("No audit-trail access for this role (least privilege).")
    else:
        try:
            evs = audit_export(svc, pid, TID)
            df = pd.DataFrame(evs)
            show = [c for c in ("event_id", "ts", "actor_id", "actor_role", "operation", "outcome", "prior_state",
                                "new_state", "reason_code", "amount_minor", "hash") if c in df.columns]
            st.dataframe(df[show].iloc[::-1], use_container_width=True, hide_index=True)
            st.download_button("Download role-filtered audit export (JSON)", json.dumps(evs, indent=2, default=str),
                               file_name=f"audit_{me.role}_{TID}.json")
        except AccessDenied as e:
            st.error(e.code)

with tab_ledger:
    try:
        lv = ledger_view(svc, me.principal_id)          # same server-side role projection as Flask /ledger
    except AccessDenied as e:
        st.error(f"{e.code} — {ROLE_LABELS[me.role]} has no access to token accounts or the ledger journal "
                 "(refused read recorded in the audit journal).")
    else:
        scope_txt = {"full": "Bank H full ledger view", "own": "own accounts and own-trade events only",
                     "metadata": "metadata only (no balances, no commercial details)"}[lv["scope"]]
        st.caption(f"Projection: {scope_txt}")
        st.write(f"Conservation check: **{'OK' if lv['integrity']['conservation_ok'] else 'FAIL'}** · "
                 f"Hash chain: **{'intact' if lv['integrity']['hash_chain_ok'] else 'BROKEN'}**")
        if lv["scope"] != "metadata":
            st.subheader("Token accounts visible to this role")
            st.dataframe(pd.DataFrame(lv["accounts"]), use_container_width=True, hide_index=True)
        if "supply" in lv:
            st.json(lv["supply"])
            st.subheader("Hash-chain verification (tamper-evident demonstration)")
            st.json(lv["journal"])
        st.subheader(f"Journal events visible to this role ({len(lv['events'])})")
        if lv["events"]:
            cols_ = [c for c in ("event_id", "ts", "actor_id", "actor_role", "operation", "outcome", "prior_state",
                                 "new_state", "reason_code") if c in lv["events"][0]]
            st.dataframe(pd.DataFrame(lv["events"])[cols_], use_container_width=True, hide_index=True)

with tab_ehkd:
    st.info("Conceptual only: Leg A = simulated tokenised commercial-bank deposits; Leg B = simulated "
            "central-bank money (e-HKD-style). Both legs commit or neither does. Not a real e-HKD, HKMA, "
            "EnsembleTX or mBridge transaction; no legal finality or FX.")
    case = st.radio("Case", list(ehkd.CASES), format_func=lambda k: f"{k} — {ehkd.CASES[k]}")
    if st.button("Execute two-leg settlement"):
        r = ehkd.run_case(case)
        (st.success if r["result"]["outcome"] == "COMMITTED_BOTH" else st.warning)(
            f"{r['result']['outcome']} {r['result']['reason']}")
        st.write(f"All-or-nothing: **{r['all_or_nothing_ok']}** · supply conserved: **{r['supply_conserved']}**")
        a, b = st.columns(2)
        a.markdown("**Leg A — tokenised deposits**")
        a.table(pd.DataFrame({"before": r["before"]["A"], "after": r["after"]["A"]}))
        b.markdown("**Leg B — CeBM (conceptual)**")
        b.table(pd.DataFrame({"before": r["before"]["B"], "after": r["after"]["B"]}))
        st.code("\n".join(r["trace"]))

with tab_about:
    st.markdown("""
**Scope.** Low-fidelity simulation of a pre-funded smart-contract escrow. The contract does *not*
verify real-world shipping or perform real KYC/AML: it consumes attestations from simulated
off-chain modules (logistics, document matching, compliance screening).

**Six states:** Created · Pending · Under Review · Frozen · Released · Refunded/Terminated.

**Release requires:** shipment PASS for this trade, documents PASS on the *current* revisions,
creation KYC/AML PASS, a fresh pre-release KYC/AML PASS (48h window), and no active hold.

**Ledger.** SQLite mock permissioned ledger with a SHA-256 hash-chained journal. Not a
distributed consensus network.
""")
