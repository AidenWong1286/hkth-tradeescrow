"""UI-layer access-control and actor-identity tests (audit P0-1, user issues 1-2).

These drive the Flask console through its HTTP interface (Flask test client), so a
direct URL cannot bypass the role projections, and they assert that every UI
action is recorded in the journal under the participant selected in the UI.
"""
from __future__ import annotations

import json

import pytest

from tradeescrow.model import AccessDenied, Role
from tradeescrow.scenarios import new_service
from tradeescrow.ui_actions import ACTIONS, ROLE_ACTIONS, autoplay_steps, run_action, run_autoplay
from tradeescrow.views import ledger_view
from ui_flask import app as flask_app

HUMANS = ["u_importer_01", "u_importer_02", "u_exporter_01", "u_bank_hk_ops", "u_bank_hk_compliance",
          "u_bank_th", "u_logistics", "u_customs", "u_regulator"]
LEDGER_ALLOWED = {"u_bank_hk_ops": "full", "u_bank_hk_compliance": "full", "u_importer_01": "own",
                  "u_importer_02": "own", "u_exporter_01": "own", "u_regulator": "metadata", "u_bank_th": "metadata"}
LEDGER_DENIED = ["u_logistics", "u_customs"]


@pytest.fixture()
def client():
    flask_app.STATE["svc"] = new_service()
    flask_app.STATE["variant"] = "clean"
    flask_app.app.config.update(TESTING=True, DEMO_CONTROLS=True)
    with flask_app.app.test_client() as c:
        yield c


def act_as(c, pid):
    c.post("/as", data={"principal": pid})


def last_event():
    return flask_app.STATE["svc"].events()[-1]


# ---------------------------------------------------------------- actor identity (user issue 2)
def test_ui_create_records_selected_importer_and_rejects_non_buyer(client):
    act_as(client, "u_importer_02")
    client.post("/act/create")
    e = last_event()
    assert e["actor_id"] == "u_importer_02" and e["outcome"] == "REJECTED" and e["reason_code"] == "NOT_TRADE_BUYER"
    assert flask_app.STATE["svc"].escrow_state("TR-001") is None
    act_as(client, "u_importer_01")
    client.post("/act/create")
    e = last_event()
    assert e["actor_id"] == "u_importer_01" and e["outcome"] == "ACCEPTED"


@pytest.mark.parametrize("variant", ["clean", "mismatch", "aml"])
def test_autoplay_every_recorded_actor_is_the_step_principal(variant):
    svc = new_service()
    results = run_autoplay(svc, variant)
    want = [who for who, a in autoplay_steps(variant) if a != "inject_aml"]
    assert [who for who, _, _ in results] == want
    for who, _, r in results:
        ev = next(e for e in svc.events() if e["event_id"] == r.event_id)
        assert ev["actor_id"] == who
    assert svc.escrow_state("TR-001") == "Released"


def test_every_offered_action_runs_as_selected_principal():
    """For each role's buttons, the journal actor equals the selected participant (accepted or refused)."""
    svc = new_service()
    run_action(svc, "create", "clean", "u_importer_01")
    pid_for = {p.role: p.principal_id for p in svc.principals()}
    for role, actions in ROLE_ACTIONS.items():
        for a in actions:
            before = len(svc.events())
            try:
                run_action(svc, a, "clean", pid_for[role])
            except Exception:
                continue
            new = svc.events()[before:]
            assert new, a
            assert all(e["actor_id"] == pid_for[role] for e in new if e["operation"] != "AUTO"), (a, new)


# ---------------------------------------------------------------- ledger projection (user issue 1 / P0-1)
@pytest.mark.parametrize("pid", list(LEDGER_ALLOWED))
def test_ledger_http_projection_by_role(client, pid):
    act_as(client, "u_importer_01")
    client.post("/act/create")
    act_as(client, pid)
    r = client.get("/ledger")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    scope = LEDGER_ALLOWED[pid]
    if scope == "full":
        assert "importer_hk_02:TDEP" in html and "exporter_th_01:TDEP" in html
    elif scope == "own":
        own = {"u_importer_01": "importer_hk_01", "u_importer_02": "importer_hk_02",
               "u_exporter_01": "exporter_th_01"}[pid]
        assert f"{own}:TDEP" in html
        for other in {"importer_hk_01", "importer_hk_02", "exporter_th_01"} - {own}:
            assert f"{other}:TDEP" not in html, (pid, other)
        assert "issued" not in html          # no aggregate supply figure
    else:  # regulator
        assert ":TDEP" not in html and "u_importer_01" not in html
        assert "40,000,000" not in html and "400,000.00" not in html


@pytest.mark.parametrize("pid", LEDGER_DENIED)
def test_ledger_http_denied_and_logged(client, pid):
    act_as(client, "u_importer_01")
    client.post("/act/create")
    act_as(client, pid)
    r = client.get("/ledger")
    assert r.status_code == 403
    html = r.get_data(as_text=True)
    assert ":TDEP" not in html and "ACCESS_DENIED" in html
    e = last_event()
    assert e["operation"] == "READ" and e["outcome"] == "REJECTED" and e["actor_id"] == pid
    assert e["details"]["attempted"] == "ledger_view"


def test_ledger_view_importer_two_sees_no_trade_events():
    svc = new_service()
    run_action(svc, "create", "clean", "u_importer_01")
    lv = ledger_view(svc, "u_importer_02")
    assert [a["owner_id"] for a in lv["accounts"]] == ["importer_hk_02"]
    assert lv["events"] == []
    with pytest.raises(AccessDenied):
        ledger_view(svc, "u_logistics")


# ---------------------------------------------------------------- export endpoint, all principals
@pytest.mark.parametrize("pid", HUMANS)
def test_export_http_respects_visibility(client, pid):
    act_as(client, "u_importer_01")
    client.post("/act/create")
    act_as(client, pid)
    r = client.get("/export.json")
    svc = flask_app.STATE["svc"]
    p = svc.principal(pid)
    if p.role in (Role.LOGISTICS, Role.CUSTOMS) or pid == "u_importer_02":
        assert r.status_code == 403
        assert json.loads(r.data)["error"] == "ACCESS_DENIED"
    else:
        assert r.status_code == 200
        data = json.loads(r.data)
        if p.role in (Role.REGULATOR, Role.BANK_TH):
            assert all("actor_id" not in e for e in data)
            assert "Harbour" not in r.get_data(as_text=True)


# ---------------------------------------------------------------- UI cannot impersonate services / off-menu actions
def test_cannot_select_service_identity(client):
    act_as(client, "svc_contract")
    client.get("/")
    act_as(client, "svc_contract")
    r = client.post("/act/settle_bank")
    assert r.status_code == 302
    assert flask_app.STATE["flash"]["code"] == "ACTION_NOT_OFFERED"   # fell back to importer, not the contract


def test_action_not_offered_to_role_is_refused(client):
    act_as(client, "u_exporter_01")
    n = len(flask_app.STATE["svc"].events())
    client.post("/act/settle_bank")
    assert flask_app.STATE["flash"]["code"] == "ACTION_NOT_OFFERED"
    assert len(flask_app.STATE["svc"].events()) == n


# ---------------------------------------------------------------- operator simulation controls
def test_sim_controls_can_be_disabled(client):
    flask_app.app.config["DEMO_CONTROLS"] = False
    for what in ("reset", "aml", "advance", "autoplay"):
        r = client.post(f"/sim/{what}")
        assert r.status_code == 403 and json.loads(r.data)["error"] == "DEMO_CONTROLS_DISABLED"
    assert "/sim/reset" not in client.get("/").get_data(as_text=True)


def test_sim_controls_refused_for_non_loopback_client(client):
    r = client.post("/sim/aml", environ_base={"REMOTE_ADDR": "10.0.0.7"})
    assert r.status_code == 403


def test_unknown_sim_control_404(client):
    assert client.post("/sim/drop_tables").status_code == 404


def test_ui_actions_catalogue_has_no_hardcoded_service_principals():
    import inspect

    from tradeescrow import ui_actions
    src = inspect.getsource(ui_actions.run_action)
    for token in ("SVC_DOCS", "SVC_KYC", "CONTRACT", "IMPORTER,", "BANK,"):
        assert token not in src
    assert set(ACTIONS) == {a for acts in ROLE_ACTIONS.values() for a in acts}


# ---------------------------------------------------------------- animated console (2026-11-19)
def _snap(html: str) -> dict:
    start = html.index('<script type="application/json" id="snap">') + len('<script type="application/json" id="snap">')
    return json.loads(html[start:html.index("</script>", start)])


@pytest.mark.parametrize("variant", ["clean", "mismatch", "aml"])
def test_film_steps_match_autoplay(client, variant):
    """Film mode (/sim/step) replays the same steps, as the same principals, to the same end state."""
    for i in range(len(autoplay_steps(variant))):
        assert client.post("/sim/step", data={"variant": variant, "i": i}).status_code == 302
    svc = flask_app.STATE["svc"]
    ref = new_service()
    run_autoplay(ref, variant)
    assert svc.escrow_state("TR-001") == ref.escrow_state("TR-001") == "Released"
    assert svc.state_path("TR-001") == ref.state_path("TR-001")
    assert [(e["actor_id"], e["operation"], e["outcome"]) for e in svc.events()] == \
           [(e["actor_id"], e["operation"], e["outcome"]) for e in ref.events()]


def test_new_sim_controls_gated(client):
    flask_app.app.config["DEMO_CONTROLS"] = False
    for what in ("step", "tamper"):
        r = client.post(f"/sim/{what}")
        assert r.status_code == 403 and json.loads(r.data)["error"] == "DEMO_CONTROLS_DISABLED"
    flask_app.app.config["DEMO_CONTROLS"] = True
    assert client.post("/sim/step", data={"i": 0}, environ_base={"REMOTE_ADDR": "10.0.0.7"}).status_code == 403
    assert client.post("/sim/step", data={"variant": "nope", "i": 0}).status_code == 404


def test_tamper_control_breaks_chain_and_reset_restores(client):
    run_autoplay(flask_app.STATE["svc"], "clean")
    assert flask_app.STATE["svc"].verify_journal()["ok"]
    client.post("/sim/tamper")
    assert not flask_app.STATE["svc"].verify_journal()["ok"]
    assert "Chain broken at" in client.get("/").get_data(as_text=True)
    client.post("/sim/reset", data={"variant": "clean"})
    assert flask_app.STATE["svc"].verify_journal()["ok"]


@pytest.mark.parametrize("pid", HUMANS)
def test_console_snapshot_and_vaults_respect_projection(client, pid):
    """The animation snapshot and the corridor vaults show only what the role's projection allows."""
    run_autoplay(flask_app.STATE["svc"], "clean")
    act_as(client, pid)
    html = client.get("/").get_data(as_text=True)
    snap = _snap(html)
    role = flask_app.STATE["svc"].principal(pid).role
    cor = snap["corridor"]
    if role in (Role.BANK_HK, Role.BANK_HK_COMPLIANCE):
        assert cor["importer"] is not None and cor["exporter"] is not None
    elif pid == "u_importer_01":
        assert cor["importer"] is not None and cor["exporter"] is None
    elif pid == "u_exporter_01":
        assert cor["exporter"] is not None and cor["importer"] is None
    else:
        assert cor["importer"] is None and cor["exporter"] is None
    if role in (Role.LOGISTICS, Role.CUSTOMS) or pid == "u_importer_02":
        assert cor["escrow"] is None and snap["events"] == []
    if pid == "u_importer_02":                       # not a party: must not even learn the escrow state
        assert snap["state"] is None and 'class="node now' not in html and 'data-state="Released"><span>' not in html
    if role in (Role.REGULATOR, Role.BANK_TH):
        assert "u_importer_01" not in json.dumps(snap) and "actor_id" not in json.dumps(snap)
