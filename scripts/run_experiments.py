"""Reproduce the full evaluation evidence bundle in results/.

    python scripts/run_experiments.py            (≈1 min; deterministic except wall-clock timings)

Outputs (all regenerated from code + fixtures):
  run_manifest.json, test_results.csv, pytest_report.xml, scenarios_summary.csv, assertions.csv,
  events/*.jsonl, metrics.csv, process_counts.csv, timelines.csv, baseline_assumptions.csv,
  control_matrix.csv, audit_completeness.csv, audit_access_matrix.csv, robustness.csv,
  mutation_analysis.csv, ehkd_results.csv, compute_time.csv, charts/*.png
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tradeescrow import ehkd, process_model as pm  # noqa: E402
from tradeescrow.model import TRANSITIONS, AccessDenied, Role, State  # noqa: E402
from tradeescrow.scenarios import (BANK, BANK_TH, COMPLIANCE, CONTRACT, CUSTOMS, EXPORTER, IMPORTER, LOGISTICS,  # noqa
                                   REGULATOR, SVC_DOCS, SVC_KYC, Flow, load_fixture, new_service,
                                   scenario_tc001, scenario_tc002, scenario_tc003)
from tradeescrow.ui_actions import ACTIONS, run_action, autoplay_steps  # noqa: E402
from tradeescrow import ui_actions as _UA  # noqa: E402
from tradeescrow.views import VISIBILITY, audit_export, redaction_probe, trade_view  # noqa: E402

RES = ROOT / "results"
TID = "TR-001"
AMT = 25_000_000
AMT_HKD = AMT / 100


def wcsv(name, rows, fields=None):
    p = RES / name
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0].keys())
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})


def code_hash() -> str:
    h = hashlib.sha256()
    for p in sorted(list((ROOT / "tradeescrow").glob("*.py")) + list((ROOT / "fixtures").glob("*.json")) +
                    list((ROOT / "ui_flask").rglob("*.py")) + list((ROOT / "ui_flask").rglob("*.html")) +
                    list((ROOT / "ui_streamlit").glob("*.py"))):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ 1 pytest
def run_pytest():
    xml = RES / "pytest_report.xml"
    p = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider",
                        f"--junitxml={xml}"], cwd=ROOT, capture_output=True, text=True)
    (RES / "pytest_output.txt").write_text(p.stdout + p.stderr)
    rows = []
    for tc in ET.parse(xml).getroot().iter("testcase"):
        status = "FAIL" if tc.find("failure") is not None or tc.find("error") is not None else \
            "SKIP" if tc.find("skipped") is not None else "PASS"
        name = tc.get("name")
        tcid = ""
        if name.startswith("test_tc"):
            tcid = "TC-" + name[7:10]
        elif name.startswith("test_eh"):
            tcid = "EH"
        rows.append({"test_id": tcid, "test_name": f"{tc.get('classname')}::{name}", "status": status,
                     "time_s": tc.get("time")})
    wcsv("test_results.csv", rows)
    return rows


# --------------------------------------------------------- 2 flagship scenarios
EXPECT = {
    "TC-001": {"fn": scenario_tc001, "path": ["Created", "Pending", "Released"],
               "importer": 15_000_000, "exporter": AMT, "escrow": 0, "blocked": 0},
    "TC-002": {"fn": lambda: scenario_tc002(resolve=None), "path": ["Created", "Pending", "Under Review"],
               "importer": 15_000_000, "exporter": 0, "escrow": AMT, "blocked": 1},
    "TC-002R": {"fn": lambda: scenario_tc002(resolve="REVALIDATE"),
                "path": ["Created", "Pending", "Under Review", "Pending", "Released"],
                "importer": 15_000_000, "exporter": AMT, "escrow": 0, "blocked": 1},
    "TC-002T": {"fn": lambda: scenario_tc002(resolve="TERMINATE"),
                "path": ["Created", "Pending", "Under Review", "Refunded/Terminated"],
                "importer": 40_000_000, "exporter": 0, "escrow": 0, "blocked": 1},
    "TC-003": {"fn": lambda: scenario_tc003(resolve=None), "path": ["Created", "Pending", "Frozen"],
               "importer": 15_000_000, "exporter": 0, "escrow": AMT, "blocked": 2},
    "TC-003C": {"fn": lambda: scenario_tc003(resolve="CLEAR"),
                "path": ["Created", "Pending", "Frozen", "Pending", "Released"],
                "importer": 15_000_000, "exporter": AMT, "escrow": 0, "blocked": 3},
    "TC-003T": {"fn": lambda: scenario_tc003(resolve="TERMINATE"),
                "path": ["Created", "Pending", "Frozen", "Refunded/Terminated"],
                "importer": 40_000_000, "exporter": 0, "escrow": 0, "blocked": 2},
}
SCEN_CLASS = {"TC-001": "normal", "TC-002R": "mismatch", "TC-003C": "aml"}


def run_scenarios():
    (RES / "events").mkdir(parents=True, exist_ok=True)
    summary, asserts, flows = [], [], {}
    for sid, e in EXPECT.items():
        f = e["fn"]()
        s = f.svc
        flows[sid] = f
        with (RES / "events" / f"{sid}.jsonl").open("w") as fh:
            for ev in s.events(TID):
                fh.write(json.dumps(ev, default=str) + "\n")
        blocked = [st for st in f.steps if "must be blocked" in st["step"] or "before fresh" in st["step"]]
        checks = [
            ("state_path", e["path"], s.state_path(TID)),
            ("importer_balance_minor", e["importer"], s.balance("importer_hk_01")),
            ("exporter_balance_minor", e["exporter"], s.balance("exporter_th_01")),
            ("escrow_balance_minor", e["escrow"], s.escrow_balance("ESC-001")),
            ("blocked_attempts_all_refused", e["blocked"], sum(1 for b in blocked if not b["ok"])),
            ("supply_conserved", True, s.supply_check()["ok"]),
            ("journal_intact", True, s.verify_journal()["ok"]),
            ("release_events", 1 if "Released" in e["path"] else 0,
             sum(1 for x in s.events(TID) if x["operation"] == "RELEASE" and x["outcome"] == "ACCEPTED")),
            ("refund_events", 1 if "Refunded/Terminated" in e["path"] else 0,
             sum(1 for x in s.events(TID) if x["operation"] == "REFUND" and x["outcome"] == "ACCEPTED")),
        ]
        ok_all = True
        for name, exp, act in checks:
            ok = exp == act
            ok_all &= ok
            asserts.append({"scenario": sid, "assertion": name, "expected": json.dumps(exp),
                            "actual": json.dumps(act), "pass": ok})
        evs = s.events(TID)
        summary.append({"scenario": sid, "expected_state_path": " > ".join(e["path"]),
                        "actual_state_path": " > ".join(s.state_path(TID)), "assertions": len(checks),
                        "assertions_passed": sum(1 for n, x, a in checks if x == a), "result": "PASS" if ok_all else "FAIL",
                        "events": len(evs), "rejected_events": sum(1 for x in evs if x["outcome"] == "REJECTED"),
                        "human_commands": sum(1 for x in evs if x["actor_kind"] == "HUMAN" and x["outcome"] == "ACCEPTED"),
                        "evidence_file": f"results/events/{sid}.jsonl"})
    wcsv("scenarios_summary.csv", summary)
    wcsv("assertions.csv", asserts)
    return summary, asserts, flows


# --------------------------------------------- 3 negative release control matrix
def control_matrix():
    rows = []

    def attempt(cid, desc, build, actor=CONTRACT):
        f = build()
        s = f.svc
        before = (s.balance("exporter_th_01"), s.escrow_balance("ESC-001") if s.escrow_state(TID) else None)
        r = s.settle(actor, TID) if s.escrow_state(TID) else None
        after = (s.balance("exporter_th_01"), s.escrow_balance("ESC-001") if s.escrow_state(TID) else None)
        blocked = (r is not None and not r.ok and before == after)
        rows.append({"control_id": cid, "unsafe_condition": desc, "actor": actor,
                     "blocked": blocked, "reason_code": r.code if r else "n/a", "funds_unchanged": before == after})

    def base(**mods):
        def b():
            f = Flow(new_service())
            for k, v in mods.get("fx", {}).items():
                f.fx[k[0]][k[1]] = v
            steps = mods.get("steps", ["create", "customs", "ship", "exporter_docs", "doc_check", "prerelease"])
            for st in steps:
                if callable(st):
                    st(f)
                else:
                    getattr(f, st)()
            return f
        return b

    attempt("NC-01", "No shipment attestation", base(steps=["create", "customs", "exporter_docs", "doc_check", "prerelease"]))
    attempt("NC-02", "Documents never checked", base(steps=["create", "customs", "ship", "exporter_docs", "prerelease"]))
    attempt("NC-03", "Document mismatch (Under Review)", base(fx={("invoice", "amount_minor"): 24_500_000}))
    attempt("NC-04", "Required customs field missing", base(steps=["create", lambda f: f.fx["customs_declaration"].pop("hs_code"),
                                                                  "customs", "ship", "exporter_docs", "doc_check", "prerelease"]))
    attempt("NC-05", "Approved documents revised afterwards",
            base(steps=["create", "customs", "ship", "exporter_docs", "doc_check", "prerelease",
                        lambda f: f.svc.submit_document(EXPORTER, TID, "INVOICE", dict(f.fx["invoice"], issue_date="2026-11-06"))]))
    attempt("NC-06", "No pre-release screening", base(steps=["create", "customs", "ship", "exporter_docs", "doc_check"]))
    attempt("NC-07", "Pre-release screening expired (49h)",
            base(steps=["create", "customs", "ship", "exporter_docs", "doc_check", "prerelease",
                        lambda f: f.svc.clock.advance(hours=49)]))
    attempt("NC-08", "Screening older than latest document approval",
            base(steps=["create", "customs", "ship", "exporter_docs", "prerelease", "doc_check"]))
    attempt("NC-09", "AML alert at pre-release (Frozen)",
            base(steps=["create", "customs", "ship", "exporter_docs", "doc_check",
                        lambda f: f.svc.sim_add_watchlist("exporter_th_01"), "prerelease"]))
    attempt("NC-10", "Manual compliance hold after all PASS",
            base(steps=["create", "customs", "ship", "exporter_docs", "doc_check", "prerelease",
                        lambda f: f.svc.raise_hold(COMPLIANCE, TID)]))
    attempt("NC-11", "Hold cleared but no fresh screening",
            base(steps=["create", "customs", "ship", "exporter_docs", "doc_check",
                        lambda f: f.svc.sim_add_watchlist("exporter_th_01"), "prerelease",
                        lambda f: f.svc.resolve_hold(COMPLIANCE, TID, "CLEAR", "AML-1")]))
    attempt("NC-12", "Already released (second release)", base(steps=["create", "customs", "ship", "exporter_docs",
                                                                     "doc_check", "prerelease", "settle"]))
    attempt("NC-13", "Already refunded", base(fx={("invoice", "amount_minor"): 24_500_000},
                                              steps=["create", "customs", "ship", "exporter_docs", "doc_check",
                                                     lambda f: f.svc.resolve_review(BANK, TID, "TERMINATE", "R")]))
    attempt("NC-14", "Regulator triggers release", base(), actor=REGULATOR)
    attempt("NC-15", "Exporter triggers release", base(), actor=EXPORTER)
    attempt("NC-16", "Importer triggers release", base(), actor=IMPORTER)
    attempt("NC-17", "Wrong-trade shipment evidence only",
            base(steps=["create", "customs", lambda f: f.svc.attest_shipment(LOGISTICS, TID, dict(
                f.fx["shipment_event"], shipment_id="SH-002", trade_id="TR-002")), "exporter_docs", "doc_check", "prerelease"]))
    # positive control: everything valid -> must release
    f = base()()
    r = f.svc.settle(CONTRACT, TID)
    rows.append({"control_id": "PC-01", "unsafe_condition": "(positive control) all gates valid", "actor": CONTRACT,
                 "blocked": not r.ok, "reason_code": r.code, "funds_unchanged": False})
    wcsv("control_matrix.csv", rows)
    return rows


# ------------------------------------------------------- 4 audit completeness
REQUIRED_FIELDS = ["event_id", "ts", "actor_id", "actor_role", "actor_kind", "operation", "outcome", "reason_code",
                   "prev_hash", "hash"]
LIFECYCLE = {
    "TC-001": [("ATTEST", "KYC_AML_CREATION_PASS"), ("CREATE", "ESCROW_CREATED"), ("LOCK", "FUNDS_LOCKED"),
               ("SUBMIT_DOCUMENT", "DOCUMENT_REVISION_STORED"), ("ATTEST", "SHIPMENT_PASS"),
               ("ATTEST", "DOCS_CONSISTENT"), ("ATTEST", "KYC_AML_PRE_RELEASE_PASS"), ("RELEASE", "ALL_GATES_PASSED"),
               ("ACKNOWLEDGE", "RECEIPT_OBSERVED_MOCK")],
    "TC-002R": [("ATTEST", "KYC_AML_CREATION_PASS"), ("CREATE", "ESCROW_CREATED"), ("LOCK", "FUNDS_LOCKED"),
                ("ATTEST", "SHIPMENT_PASS"), ("REVIEW", "DOC_AMOUNT_MISMATCH"), ("SETTLE", "ESCROW_UNDER_REVIEW"),
                ("REVOKE_ATTESTATION", "STALE_DOCUMENT_APPROVAL"), ("ATTEST", "DOCS_CONSISTENT"),
                ("REVIEW", "REVIEW_REVALIDATED"), ("ATTEST", "KYC_AML_PRE_RELEASE_PASS"), ("RELEASE", "ALL_GATES_PASSED")],
    "TC-003C": [("ATTEST", "KYC_AML_CREATION_PASS"), ("CREATE", "ESCROW_CREATED"), ("LOCK", "FUNDS_LOCKED"),
                ("ATTEST", "SHIPMENT_PASS"), ("ATTEST", "DOCS_CONSISTENT"), ("FREEZE", "SANCTIONS_FLAG_SIMULATED"),
                ("SETTLE", "ESCROW_FROZEN"), ("RESOLVE_REVIEW", "ACTIVE_HOLD"), ("REVIEW", "HOLD_CLEARED_FALSE_POSITIVE"),
                ("SETTLE", "PRE_RELEASE_KYC_MISSING"), ("ATTEST", "KYC_AML_PRE_RELEASE_PASS"),
                ("RELEASE", "ALL_GATES_PASSED")],
}


def audit_checks(flows):
    rows = []
    for sid, req in LIFECYCLE.items():
        s = flows[sid].svc
        evs = s.events(TID)
        present = 0
        for op, code in req:
            hit = [e for e in evs if e["operation"] == op and e["reason_code"] == code]
            ok = bool(hit) and all(all(e.get(k) not in (None, "") for k in REQUIRED_FIELDS) for e in hit)
            if op in ("CREATE", "LOCK", "RELEASE", "REFUND"):
                ok = ok and all(e["amount_minor"] for e in hit)
            present += ok
        fields_ok = sum(1 for e in evs if all(e.get(k) not in (None, "") for k in REQUIRED_FIELDS))
        reg = audit_export(s, REGULATOR, TID)
        path = []
        for e in reg:
            if e["outcome"] == "ACCEPTED" and e["new_state"] and (not path or path[-1] != e["new_state"]):
                path.append(e["new_state"])
        fx = load_fixture()
        leaks = redaction_probe(reg, [fx["contract"]["goods_description"], "unit_price_minor", "u_importer_01",
                                      "u_exporter_01", "Harbour Kitchenware"])
        rows.append({"scenario": sid, "required_lifecycle_events": len(req), "present_with_required_fields": present,
                     "audit_completeness_pct": round(100 * present / len(req), 1),
                     "events_total": len(evs), "events_with_all_required_fields": fields_ok,
                     "rejected_attempts_logged": sum(1 for e in evs if e["outcome"] == "REJECTED"),
                     "regulator_reconstructs_state_path": path == s.state_path(TID),
                     "regulator_export_commercial_leaks": len(leaks),
                     "hash_chain_intact": s.verify_journal()["ok"]})
    wcsv("audit_completeness.csv", rows)
    return rows


# ------------------------------------------------------------ 5 access matrix
def access_matrix(flows):
    s = flows["TC-002R"].svc
    principals = {"IMPORTER (own trade)": "u_importer_01", "IMPORTER (other trade)": "u_importer_02",
                  "EXPORTER": "u_exporter_01", "BANK_HK": "u_bank_hk_ops", "BANK_HK_COMPLIANCE": "u_bank_hk_compliance",
                  "BANK_TH": "u_bank_th", "LOGISTICS": "u_logistics", "CUSTOMS": "u_customs", "REGULATOR": "u_regulator"}
    # expected policy (the specification the code must obey)
    expected = {
        "IMPORTER (own trade)": dict(view=1, amount=1, doc_bodies=1, compliance_reasons=0, audit=1, guard=0, commercial_terms=1),
        "IMPORTER (other trade)": dict(view=0, amount=0, doc_bodies=0, compliance_reasons=0, audit=0, guard=0, commercial_terms=0),
        "EXPORTER": dict(view=1, amount=1, doc_bodies=1, compliance_reasons=0, audit=1, guard=0, commercial_terms=1),
        "BANK_HK": dict(view=1, amount=1, doc_bodies=1, compliance_reasons=1, audit=1, guard=1, commercial_terms=1),
        "BANK_HK_COMPLIANCE": dict(view=1, amount=1, doc_bodies=1, compliance_reasons=1, audit=1, guard=1, commercial_terms=1),
        "BANK_TH": dict(view=1, amount=1, doc_bodies=0, compliance_reasons=0, audit=1, guard=0, commercial_terms=0),
        "LOGISTICS": dict(view=1, amount=0, doc_bodies=0, compliance_reasons=0, audit=0, guard=0, commercial_terms=0),
        "CUSTOMS": dict(view=1, amount=0, doc_bodies=0, compliance_reasons=0, audit=0, guard=0, commercial_terms=0),
        "REGULATOR": dict(view=1, amount=1, doc_bodies=0, compliance_reasons=1, audit=1, guard=0, commercial_terms=0),
    }
    rows = []
    for label, pid in principals.items():
        try:
            v = trade_view(s, pid, TID)
            got = dict(view=1, amount=int("amount_minor" in v),
                       doc_bodies=int(any("content" in d for d in v.get("documents", []))),
                       compliance_reasons=int(any("reason_code" in a for a in v.get("attestations", [])
                                                  if a.get("type") == "KYC_AML")),
                       guard=int("release_guard" in v), commercial_terms=int("contract_terms" in v))
        except AccessDenied:
            got = dict(view=0, amount=0, doc_bodies=0, compliance_reasons=0, guard=0, commercial_terms=0)
        if VISIBILITY.get(s.principal(pid).role, {}).get("events") == "none":
            got["audit"] = 0
        else:
            try:
                audit_export(s, pid, TID)
                got["audit"] = 1
            except AccessDenied:
                got["audit"] = 0
        for k, exp in expected[label].items():
            rows.append({"role": label, "capability": k, "expected": exp, "actual": got[k], "obeyed": exp == got[k]})
    wcsv("audit_access_matrix.csv", rows)
    return rows


# --------------------------------------------- 6 process model comparison
def process_comparison():
    counts, tl = [], []
    for scen in ("normal", "mismatch", "aml"):
        for model in ("baseline", "proposed", "proposed_e2e"):
            ts = pm.tasks_for(model, scen)
            settle = [t for t in ts if t.segment == "SETTLEMENT" and t.kind != "WAIT"]
            counts.append({"scenario": scen, "model": model, "model_label": pm.MODEL_LABELS[model],
                           "evidence_type": "TEAM-DEFINED PROCESS MODEL (not measured industry savings)",
                           "tasks_total": len([t for t in ts if t.kind != "WAIT"]),
                           "settlement_tasks": len(settle),
                           "manual_settlement_tasks": sum(1 for t in settle if t.kind == "MANUAL"),
                           "automated_settlement_tasks": sum(1 for t in settle if t.kind == "AUTO"),
                           "manual_incl_common": sum(1 for t in ts if t.kind in ("MANUAL", "EXTERNAL_MANUAL")),
                           "gateways": len(pm.GATEWAYS.get(model, pm.GATEWAYS["proposed"])),
                           "manual_task_ids": " ".join(t.id for t in settle if t.kind == "MANUAL")})
            for level in ("low", "base", "high"):
                for term in (0, 30):
                    m = pm.timeline(model, scen, level, term)
                    prefund = max(0.0, m["SHIPMENT"] - m["FUNDED"]) if m["FUNDED"] < m["SHIPMENT"] else 0.0
                    exporter_unsecured = (m["CREDITED"] - m["SHIPMENT"]) if model == "baseline" else 0.0
                    importer_locked = (m["CREDITED"] - m["FUNDED"])
                    tl.append({"scenario": scen, "model": model,
                               "evidence_type": "ASSUMPTION-DRIVEN TIMING (team durations; not bank performance)",
                               "assumption_level": level, "payment_term_days": term,
                               "t_funded_d": round(m["FUNDED"], 2), "t_shipment_d": round(m["SHIPMENT"], 2),
                               "t_credited_d": round(m["CREDITED"], 2),
                               "full_cycle_to_credit_d": round(m["CREDITED"], 2),
                               "post_shipment_latency_d": round(m["CREDITED"] - m["SHIPMENT"], 2),
                               "importer_funds_committed_d": round(importer_locked, 2),
                               "importer_prefunding_before_shipment_d": round(prefund, 2),
                               "importer_lockup_hkd_days": round(AMT_HKD * importer_locked),
                               "exporter_unsecured_receivable_d": round(exporter_unsecured, 2),
                               "exporter_unsecured_hkd_days": round(AMT_HKD * exporter_unsecured)})
    wcsv("process_counts.csv", counts)
    wcsv("timelines.csv", tl)
    rows = []
    for model, (_, tasks) in pm.ALL_MODELS.items():
        for t in tasks:
            rows.append({"model": model, "task_id": t.id, "lane": t.lane, "task": t.name, "kind": t.kind,
                         "segment": t.segment, "path": t.path, "dur_low_d": t.dur[0], "dur_base_d": t.dur[1],
                         "dur_high_d": t.dur[2], "milestone": t.milestone or "",
                         "source": ("TEAM ASSUMPTION; HYPOTHETICAL step, not implemented in prototype; duration copied "
                                    "from the equivalent baseline step") if t.id.endswith("h") else
                                   "TEAM ASSUMPTION (illustrative; fixed before comparison; not empirical)"})
    wcsv("baseline_assumptions.csv", rows)
    return counts, tl


def measured_human(flows):
    """Counts COMMANDS (Flow steps) accepted from human roles, not journal events
    (one command can emit several events, e.g. CREATE + LOCK + contract upload)."""
    from tradeescrow.model import HUMAN_ROLES
    out = []
    for sid, cls in SCEN_CLASS.items():
        f = flows[sid]
        role = {p.principal_id: p.role for p in f.svc.principals()}
        hum = [st for st in f.steps if st["ok"] and role.get(st["actor"]) in HUMAN_ROLES]
        common = [st for st in hum if role[st["actor"]] in ("CUSTOMS", "LOGISTICS")]
        auto = [st for st in f.steps if st["ok"] and role.get(st["actor"]) not in HUMAN_ROLES]
        out.append({"scenario": sid, "class": cls, "human_commands_total": len(hum),
                    "human_commands_settlement": len(hum) - len(common), "human_commands_common": len(common),
                    "automated_service_commands": len(auto),
                    "human_command_list": " | ".join(f"{role[st['actor']]}:{st['step']}" for st in hum)})
    return out


# ------------------------------------------------- 7 randomized robustness
def robustness(n_trades=200, steps=30, seed=3002):
    rng = random.Random(seed)
    acts = list(ACTIONS)
    totals = {"trades": 0, "commands": 0, "accepted": 0, "rejected": 0, "invariant_checks": 0, "violations": 0, "harness_errors": 0}
    principals = sorted({v[1] for v in ACTIONS.values()})
    outcomes = {}
    viol_examples = []
    for i in range(n_trades):
        s = new_service()
        variant = rng.choice(["clean", "mismatch", "aml"])
        # canonical path = the scenario's own (principal, action) script; each step runs as its real owner
        canon = list(autoplay_steps(variant))
        for _ in range(steps):
            r = rng.random()
            if r < 0.05:
                s.sim_add_watchlist(rng.choice(["exporter_th_01", "importer_hk_01"]), "SANCTIONS_FLAG_SIMULATED")
            elif r < 0.10:
                s.clock.advance(hours=rng.choice([1, 24, 50]))
            else:
                # guided random walk: 60% next canonical step for the variant, 40% any action (incl. forbidden)
                if rng.random() < 0.6 and canon:
                    who, a = canon.pop(0)
                    if a == "inject_aml":
                        s.sim_add_watchlist("exporter_th_01", "SANCTIONS_FLAG_SIMULATED")
                        continue
                else:
                    # any action, by its owner (50%) or by a random participant (exercises RBAC refusals)
                    a = rng.choice(acts)
                    who = ACTIONS[a][1] if rng.random() < 0.5 else rng.choice(principals)
                s.clock.advance(minutes=30)
                try:
                    res = run_action(s, a, variant, who)
                    totals["commands"] += 1
                    totals["accepted" if res.ok else "rejected"] += 1
                except (TypeError, AttributeError, NameError):
                    totals["harness_errors"] += 1     # a broken harness must never be scored as "rejected"
                    raise
                except Exception:  # domain refusals raised as exceptions (e.g. UNKNOWN_TRADE before creation)
                    totals["commands"] += 1
                    totals["rejected"] += 1
            # invariants after every step
            totals["invariant_checks"] += 1
            bad = []
            if not s.supply_check()["ok"]:
                bad.append("conservation")
            evs = s.events(TID) if s.escrow_state(TID) else []
            for e in evs:
                if e["outcome"] == "ACCEPTED" and e["prior_state"] != e["new_state"] and \
                        (e["prior_state"], e["new_state"]) not in TRANSITIONS:
                    bad.append("illegal_transition")
                if e["operation"] == "RELEASE" and e["outcome"] == "ACCEPTED" and \
                        not all(g["ok"] for g in e["details"]["guard"]["gates"]):
                    bad.append("release_without_all_gates")
            rel = sum(1 for e in evs if e["operation"] == "RELEASE" and e["outcome"] == "ACCEPTED")
            ref = sum(1 for e in evs if e["operation"] == "REFUND" and e["outcome"] == "ACCEPTED")
            if rel + ref > 1:
                bad.append("double_settlement")
            if s.escrow_state(TID) == State.FROZEN and rel:
                bad.append("released_while_frozen")
            if bad:
                totals["violations"] += 1
                viol_examples.append((i, bad))
        if not s.verify_journal()["ok"]:
            totals["violations"] += 1
        totals["trades"] += 1
        st = s.escrow_state(TID) or "No escrow"
        outcomes[st] = outcomes.get(st, 0) + 1
    rows = [{"metric": k, "value": v} for k, v in totals.items()] + \
           [{"metric": f"final_state::{k}", "value": v} for k, v in sorted(outcomes.items())] + \
           [{"metric": "seed", "value": seed}, {"metric": "steps_per_trade", "value": steps}]
    wcsv("robustness.csv", rows)
    return totals, outcomes


# ------------------------------------------------------- 8 mutation analysis
MUTANTS = [
    ("M01", "Release guard ignores active holds", "escrow.py", 'gate("no_active_hold", not holds,', 'gate("no_active_hold", True,'),
    ("M02", "Document approval not pinned to current revision", "escrow.py",
     'd["result"] == "PASS" and d["input_digest"] == self._docs_digest(meta),\n             "DOCUMENTS_NOT_VERIFIED"',
     'd["result"] == "PASS",\n             "DOCUMENTS_NOT_VERIFIED"'),
    ("M03", "Pre-release screening never expires", "escrow.py", 'k2["expires_at"] > now,', 'True,'),
    ("M04", "Server-side RBAC disabled", "escrow.py", "if p.role not in PERMISSIONS[op]:", "if False:"),
    ("M05", "Screening freshness ordering removed", "escrow.py", 'gate("kyc_prerelease_pass", k2 and fresh_order,', 'gate("kyc_prerelease_pass", k2,'),
    ("M06", "Cross-trade shipment check removed", "escrow.py",
     'or shipment.get("shipment_id") != trade["shipment_id"]:', ':'),
    ("M07", "New document revision does not revoke approvals", "escrow.py", "if stale and rev > 1:", "if False:"),
    ("M08", "Creation KYC/AML not enforced", "escrow.py", 'if screen["result"] != "PASS":', "if False:"),
    ("M09", "Hash verification skips content check", "escrow.py",
     'if offchain.digest(rec) != r["hash"]:', 'if False:'),
    ("M10", "Regulator receives full events", "views.py",
     'if pol["events"] in ("full", "full_own"):', 'if True:'),
    ("M11", "Optimistic version check removed", "escrow.py",
     '"WHERE escrow_id=? AND state=? AND version=?",\n                      (to_state, self.clock.iso(), esc["escrow_id"], frm, esc["version"])',
     '"WHERE escrow_id=?",\n                      (to_state, self.clock.iso(), esc["escrow_id"])'),
    ("M12", "Refund allowed during AML hold", "escrow.py",
     'if esc["state"] == State.FROZEN or self._active_holds(c, esc["escrow_id"]):\n                raise Rejection("ACTIVE_HOLD"',
     'if False:\n                raise Rejection("ACTIVE_HOLD"'),
    ("M13", "Document matching ignores amounts", "offchain.py", 'same("DOC_AMOUNT_MISMATCH"', '(lambda *a: None)("DOC_AMOUNT_MISMATCH"'),
    ("M14", "Idempotency store disabled", "escrow.py", "if command_id:\n                r = c.execute", "if False:\n                r = c.execute"),
]


def _sandbox() -> Path:
    tmp = Path(tempfile.mkdtemp())
    for d in ("tradeescrow", "tests", "fixtures", "ui_flask"):
        shutil.copytree(ROOT / d, tmp / d, ignore=shutil.ignore_patterns("__pycache__"))
    return tmp


def _pytest(cwd):
    return subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-x", "-p", "no:cacheprovider"],
                          cwd=cwd, capture_output=True, text=True, timeout=300)


def mutation_analysis():
    # Guard against spurious kills: the UNMUTATED sandbox must pass first (e.g. a missing package
    # in the sandbox would otherwise make every mutant look 'killed' via a collection error).
    tmp = _sandbox()
    clean = _pytest(tmp)
    shutil.rmtree(tmp)
    if clean.returncode != 0:
        raise SystemExit("mutation sandbox fails WITHOUT mutation; fix sandbox before trusting results:\n"
                         + clean.stdout[-2000:])
    rows = []
    for mid, desc, fname, old, new in MUTANTS:
        tmp = _sandbox()
        p = tmp / "tradeescrow" / fname
        src = p.read_text()
        applied = old in src
        p.write_text(src.replace(old, new, 1))
        r = _pytest(tmp)
        killed = r.returncode == 1          # 1 = tests failed; 2+ = collection/usage error (not a kill)
        if r.returncode not in (0, 1):
            raise SystemExit(f"{mid}: pytest exit {r.returncode} (collection error) — result not trustworthy")
        first_fail = ""
        for line in r.stdout.splitlines():
            if line.startswith("FAILED"):
                first_fail = line.split("::")[-1].split(" ")[0]
                break
        rows.append({"mutant": mid, "seeded_defect": desc, "file": fname, "applied": applied,
                     "killed_by_suite": killed, "first_failing_test": first_fail})
        shutil.rmtree(tmp)
    wcsv("mutation_analysis.csv", rows)
    return rows


# -------------------------------------------------------------- 9 e-HKD, timing
def ehkd_results():
    rows = []
    for case in ehkd.CASES:
        r = ehkd.run_case(case)
        rows.append({"case": case, "description": r["description"], "outcome": r["result"]["outcome"],
                     "leg_a_changed": r["leg_a_changed"], "leg_b_changed": r["leg_b_changed"],
                     "all_or_nothing_ok": r["all_or_nothing_ok"], "supply_conserved": r["supply_conserved"],
                     "no_reservations_left": r["no_reservations_left"]})
    wcsv("ehkd_results.csv", rows)
    return rows


def compute_time(reps=30):
    rows = []
    for sid in ("TC-001", "TC-002R", "TC-003C"):
        ts = []
        for _ in range(reps):
            t = time.perf_counter()
            EXPECT[sid]["fn"]()
            ts.append((time.perf_counter() - t) * 1000)
        rows.append({"scenario": sid, "reps": reps, "median_ms": round(statistics.median(ts), 2),
                     "min_ms": round(min(ts), 2), "max_ms": round(max(ts), 2),
                     "note": "WALL-CLOCK engine compute incl. fresh in-memory DB setup; not business settlement time"})
    wcsv("compute_time.csv", rows)
    return rows


# ------------------------------------------------------------------ charts
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1f2937", "#6b7280", "#e5e7eb"


def charts(counts, tl, ctrl, mut, tests):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cdir = RES / "charts"
    cdir.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})

    def style(ax):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)

    # 1 manual settlement tasks (three models incl. matched-scope sensitivity)
    GREY = "#8a94a6"
    fig, ax = plt.subplots(figsize=(7.6, 4.0), dpi=200)
    scen = ["normal", "mismatch", "aml"]
    lab = ["Normal", "Document mismatch", "AML alert"]
    series = [("baseline", BLUE, "Baseline open account"),
              ("proposed", ORANGE, "Escrow, prototype scope (Bank O observes)"),
              ("proposed_e2e", GREY, "Escrow + hypothetical cross-bank leg (matched scope)")]
    w = 0.26
    for k, (model, col, lbl) in enumerate(series):
        vals = [next(c["manual_settlement_tasks"] for c in counts if c["scenario"] == s_ and c["model"] == model)
                for s_ in scen]
        bars = ax.bar([i + (k - 1) * w for i in range(3)], vals, w * 0.92, color=col, label=lbl,
                      hatch="//" if model == "proposed_e2e" else None, edgecolor="white")
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.1, f"{int(r.get_height())}", ha="center",
                    fontsize=9, color=INK)
    ax.set_xticks(range(3), lab)
    ax.set_ylabel("Manual settlement tasks (count)")
    ax.set_ylim(0, 11)
    ax.set_title("Manual settlement tasks per transaction — TEAM-DEFINED PROCESS MODEL; not measured industry savings\n"
                 "(BPMN task inventory; common goods/customs/carriage tasks excluded; FX excluded in all models)",
                 fontsize=8.6, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    style(ax)
    fig.tight_layout()
    fig.savefig(cdir / "manual_tasks.png")
    plt.close(fig)

    # 2a post-shipment latency
    fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
    for k, term in enumerate((0, 30)):
        for j, model in enumerate(("baseline", "proposed")):
            def pick(level, s):
                return next(r for r in tl if r["scenario"] == s and r["model"] == model and
                            r["assumption_level"] == level and r["payment_term_days"] == term)["post_shipment_latency_d"]
            vals = [pick("base", s) for s in scen]
            lows = [pick("low", s) for s in scen]
            highs = [pick("high", s) for s in scen]
            xs = [i + (k * 2 + j - 1.5) * 0.19 for i in range(3)]
            ax.bar(xs, vals, 0.17, color=BLUE if model == "baseline" else ORANGE, alpha=1.0 if term == 0 else 0.45,
                   label=f"{'Baseline open account' if model == 'baseline' else 'Proposed escrow'}, payment term {term}d")
            ax.errorbar(xs, vals, yerr=[[v - l for v, l in zip(vals, lows)], [h - v for v, h in zip(vals, highs)]],
                        fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
    ax.set_xticks(range(3), lab)
    ax.set_ylabel("Simulated days")
    ax.set_title("Post-shipment latency to exporter credit — ASSUMPTION-DRIVEN MODEL, simulated days, not bank timings\n"
                 "(bar = base assumption; whiskers = low–high; escrow is unaffected by the payment term)",
                 fontsize=9, loc="left", color=INK)
    ax.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    style(ax)
    fig.tight_layout()
    fig.savefig(cdir / "timing_tradeoff.png")
    plt.close(fig)

    # 2b who carries the financing burden (normal scenario)
    AQUA, YEL = "#1baf7a", "#eda100"
    cats = [("Baseline, term 0d", "baseline", 0), ("Baseline, term 30d", "baseline", 30),
            ("Escrow (prototype scope)", "proposed", 0), ("Escrow + cross-bank leg\n(hypothetical)", "proposed_e2e", 0)]
    fig, ax = plt.subplots(figsize=(7.6, 3.8), dpi=200)
    for i, (name, model, term) in enumerate(cats):
        for j, (field, col, lbl) in enumerate((("importer_funds_committed_d", AQUA, "Importer cash committed before exporter is credited"),
                                               ("exporter_unsecured_receivable_d", YEL, "Exporter shipped but unpaid with no payment security"))):
            def pick(level):
                return next(r for r in tl if r["scenario"] == "normal" and r["model"] == model and
                            r["assumption_level"] == level and r["payment_term_days"] == term)[field]
            v, lo, hi = pick("base"), pick("low"), pick("high")
            x = i + (j - 0.5) * 0.36
            ax.bar(x, v, 0.34, color=col, label=lbl if i == 0 else None)
            ax.errorbar([x], [v], yerr=[[v - lo], [hi - v]], fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
            ax.text(x, hi + 0.8, f"{v:g}", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(cats)), [c[0] for c in cats], fontsize=8.5)
    ax.set_ylabel("Simulated days (normal scenario)")
    ax.set_title("Who carries the financing burden? Escrow shifts it from exporter to importer\n"
                 "(ASSUMPTION-DRIVEN MODEL; ×HKD 250,000 gives HKD-days; base assumption, whiskers low–high)",
                 fontsize=9, loc="left", color=INK)
    ax.legend(frameon=False, fontsize=7.8, loc="upper left")
    style(ax)
    fig.tight_layout()
    fig.savefig(cdir / "financing_burden.png")
    plt.close(fig)

    # 3 controls & tests summary (horizontal bars with denominators)
    neg = [c for c in ctrl if c["control_id"].startswith("NC")]
    items = [("Automated tests passed", sum(t["status"] == "PASS" for t in tests), len(tests)),
             ("Unsafe release attempts blocked", sum(bool(c["blocked"]) for c in neg), len(neg)),
             ("Seeded defects detected (mutation)", sum(bool(m["killed_by_suite"]) for m in mut), len(mut))]
    fig, ax = plt.subplots(figsize=(7.2, 2.4), dpi=200)
    for i, (name, n, d) in enumerate(items):
        ax.barh(i, d, color=GRID, height=0.5)
        ax.barh(i, n, color=ORANGE if i else BLUE, height=0.5)
        ax.text(d + 0.4, i, f"{n} / {d}", va="center", fontsize=9.5, color=INK)
    ax.set_yticks(range(len(items)), [i[0] for i in items])
    ax.invert_yaxis()
    ax.set_xlim(0, max(i[2] for i in items) * 1.18)
    ax.set_xlabel("count")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Verification results (actual run outputs; denominators shown)", fontsize=9.5, loc="left", color=INK)
    fig.tight_layout()
    fig.savefig(cdir / "verification_summary.png")
    plt.close(fig)


# ------------------------------------------------------------------- main
def main():
    RES.mkdir(exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    tests = run_pytest()
    summary, asserts, flows = run_scenarios()
    ctrl = control_matrix()
    audit = audit_checks(flows)
    access = access_matrix(flows)
    counts, tl = process_comparison()
    human = measured_human(flows)
    wcsv("measured_human_commands.csv", human)
    rob, outcomes = robustness()
    mut = mutation_analysis()
    eh = ehkd_results()
    ct = compute_time()

    def get(model, scen, field, level="base", term=0):
        return next(r for r in tl if r["model"] == model and r["scenario"] == scen and r["assumption_level"] == level
                    and r["payment_term_days"] == term)[field]

    def cnt(model, scen, field):
        return next(c for c in counts if c["model"] == model and c["scenario"] == scen)[field]

    def pct(a, b):
        return "not defined" if b == 0 else round(100 * (b - a) / b, 1)

    neg = [c for c in ctrl if c["control_id"].startswith("NC")]
    metrics = [
        ("M-01", "Automated tests passed", sum(t["status"] == "PASS" for t in tests), len(tests), "tests", "SIMULATION_RESULT", "test_results.csv"),
        ("M-02", "Flagship scenario assertions passed", sum(a["pass"] for a in asserts), len(asserts), "assertions", "SIMULATION_RESULT", "assertions.csv"),
        ("M-03", "Transition/outcome accuracy (%)", round(100 * sum(a["pass"] for a in asserts) / len(asserts), 1), "", "%", "SIMULATION_RESULT", "assertions.csv"),
        ("M-04", "Unsafe release attempts blocked", sum(bool(c["blocked"]) for c in neg), len(neg), "attempts", "SIMULATION_RESULT", "control_matrix.csv"),
        ("M-05", "Positive control released", not next(c for c in ctrl if c["control_id"] == "PC-01")["blocked"], "", "bool", "SIMULATION_RESULT", "control_matrix.csv"),
        ("M-06", "Audit completeness, lifecycle events (sum over 3 scenarios)", sum(a["present_with_required_fields"] for a in audit),
         sum(a["required_lifecycle_events"] for a in audit), "events", "SIMULATION_RESULT", "audit_completeness.csv"),
        ("M-07", "Regulator reconstructs state path from metadata only", sum(bool(a["regulator_reconstructs_state_path"]) for a in audit), len(audit), "scenarios", "SIMULATION_RESULT", "audit_completeness.csv"),
        ("M-08", "Role-visibility rules obeyed", sum(bool(a["obeyed"]) for a in access), len(access), "rules", "SIMULATION_RESULT", "audit_access_matrix.csv"),
        ("M-09", "Random-sequence invariant violations", rob["violations"], rob["invariant_checks"], "checks", "SIMULATION_RESULT", "robustness.csv"),
        ("M-10", "Random commands executed (200 trades, seed 3002)", rob["commands"], "", "commands", "SIMULATION_RESULT", "robustness.csv"),
        ("M-11", "Seeded defects detected by test suite", sum(bool(m["killed_by_suite"]) for m in mut), len(mut), "mutants", "SIMULATION_RESULT", "mutation_analysis.csv"),
        ("M-12", "e-HKD cases satisfying all-or-nothing", sum(bool(e["all_or_nothing_ok"]) for e in eh), len(eh), "cases", "SIMULATION_RESULT", "ehkd_results.csv"),
        ("M-13", "Manual settlement tasks — baseline, normal", cnt("baseline", "normal", "manual_settlement_tasks"), "", "tasks", "MODEL (BPMN inventory)", "process_counts.csv"),
        ("M-14", "Manual settlement tasks — escrow, normal", cnt("proposed", "normal", "manual_settlement_tasks"), "", "tasks", "MODEL (BPMN inventory)", "process_counts.csv"),
        ("M-15", "Manual-step reduction, normal (%)", pct(cnt("proposed", "normal", "manual_settlement_tasks"), cnt("baseline", "normal", "manual_settlement_tasks")), "", "%", "MODEL", "process_counts.csv"),
        ("M-16", "Manual settlement tasks — baseline, mismatch", cnt("baseline", "mismatch", "manual_settlement_tasks"), "", "tasks", "MODEL", "process_counts.csv"),
        ("M-17", "Manual settlement tasks — escrow, mismatch", cnt("proposed", "mismatch", "manual_settlement_tasks"), "", "tasks", "MODEL", "process_counts.csv"),
        ("M-18", "Manual settlement tasks — baseline, AML", cnt("baseline", "aml", "manual_settlement_tasks"), "", "tasks", "MODEL", "process_counts.csv"),
        ("M-19", "Manual settlement tasks — escrow, AML", cnt("proposed", "aml", "manual_settlement_tasks"), "", "tasks", "MODEL", "process_counts.csv"),
        ("M-20", "Human settlement-role commands executed in prototype, TC-001", next(h for h in human if h["scenario"] == "TC-001")["human_commands_settlement"], "", "commands", "SIMULATION_RESULT", "measured_human_commands.csv"),
        ("M-21", "Post-shipment latency — baseline, normal, base, term 0 (days)", get("baseline", "normal", "post_shipment_latency_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-22", "Post-shipment latency — escrow, normal, base (days)", get("proposed", "normal", "post_shipment_latency_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-23", "Post-shipment latency — baseline, normal, base, term 30 (days)", get("baseline", "normal", "post_shipment_latency_d", term=30), "", "sim days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-24", "Importer funds committed before exporter credit — baseline, normal, base, term 0 (days)", get("baseline", "normal", "importer_funds_committed_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-25", "Importer funds committed before exporter credit — escrow, normal, base (days)", get("proposed", "normal", "importer_funds_committed_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-26", "Importer lock-up — escrow, normal, base (HKD-days)", get("proposed", "normal", "importer_lockup_hkd_days"), "", "HKD-days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-27", "Exporter unsecured receivable — baseline, normal, base, term 30 (HKD-days)", get("baseline", "normal", "exporter_unsecured_hkd_days", term=30), "", "HKD-days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-28", "Full cycle to exporter credit — baseline, normal, base, term 0 (days)", get("baseline", "normal", "full_cycle_to_credit_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-29", "Full cycle to exporter credit — escrow, normal, base (days)", get("proposed", "normal", "full_cycle_to_credit_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL", "timelines.csv"),
        ("M-30", "Engine compute TC-001 median (ms, wall-clock)", next(c for c in ct if c["scenario"] == "TC-001")["median_ms"], "", "ms", "SIMULATION_RESULT (environment-dependent)", "compute_time.csv"),
        ("M-31", "Manual settlement tasks — escrow + hypothetical cross-bank leg (matched scope), normal", cnt("proposed_e2e", "normal", "manual_settlement_tasks"), "", "tasks", "MODEL — SENSITIVITY (hypothetical steps)", "process_counts.csv"),
        ("M-32", "Manual-step reduction, matched scope, normal (%)", pct(cnt("proposed_e2e", "normal", "manual_settlement_tasks"), cnt("baseline", "normal", "manual_settlement_tasks")), "", "%", "MODEL — SENSITIVITY", "process_counts.csv"),
        ("M-33", "Post-shipment latency to Bank O credit — matched scope, normal, base (days)", get("proposed_e2e", "normal", "post_shipment_latency_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL — SENSITIVITY", "timelines.csv"),
        ("M-34", "Importer funds committed before Bank O credit — matched scope, normal, base (days)", get("proposed_e2e", "normal", "importer_funds_committed_d"), "", "sim days", "ASSUMPTION-DRIVEN MODEL — SENSITIVITY", "timelines.csv"),
    ]
    wcsv("metrics.csv", [{"metric_id": m[0], "metric": m[1], "value": m[2], "denominator": m[3], "unit": m[4],
                          "claim_type": m[5], "source_file": f"results/{m[6]}"} for m in metrics])
    charts(counts, tl, ctrl, mut, tests)
    manifest = {"run_started_utc": started, "run_finished_utc": datetime.now(timezone.utc).isoformat(),
                "code_sha256_16": code_hash(), "fixture_version": load_fixture()["fixture_version"],
                "python": platform.python_version(), "platform": platform.platform(),
                "random_seed_robustness": 3002, "sim_clock_start": "2026-11-02T09:00:00+08:00",
                "rule_config": {"txn_limit_minor": 500_000_000, "prerelease_kyc_validity_hours": 48, "currency": "HKD",
                                "note": "HKD 5,000,000 limit and 48h screening window are TEAM PARAMETERS, not "
                                        "HKMA or legal requirements"},
                "evidence_legend": {"SIMULATION_RESULT": "executed tests / runs of this code on synthetic data",
                                    "MODEL": "team-defined BPMN process inventory; not measured industry savings",
                                    "ASSUMPTION-DRIVEN MODEL": "team-assumed durations; not bank performance",
                                    "SENSITIVITY": "includes hypothetical steps the prototype does not implement"},
                "note": "Business durations are assumption-driven (results/baseline_assumptions.csv). Wall-clock timings "
                        "(compute_time.csv) are environment-dependent and are not settlement times."}
    (RES / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({m[0]: [m[1], m[2], m[3]] for m in metrics}, indent=0))


if __name__ == "__main__":
    main()
