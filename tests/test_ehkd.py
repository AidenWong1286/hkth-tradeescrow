"""Tests for the conceptual e-HKD two-leg atomic settlement (EH-01..EH-05)."""
import pytest

from tradeescrow.ehkd import CASES, run_case


@pytest.mark.parametrize("case", list(CASES))
def test_eh_all_or_nothing(case):
    r = run_case(case)
    assert r["all_or_nothing_ok"]
    assert r["supply_conserved"]
    assert r["no_reservations_left"]


def test_eh01_success_moves_both_legs():
    r = run_case("success")
    assert r["result"]["outcome"] == "COMMITTED_BOTH"
    assert r["after"]["A"]["exporter_th_01@BankO"] == 25_000_000
    assert r["after"]["B"]["BankO:CeBM"] - r["before"]["B"]["BankO:CeBM"] == 25_000_000


@pytest.mark.parametrize("case", ["cebm_insufficient", "deposit_leg_refused", "crash_before_decision"])
def test_eh_failures_roll_back_both(case):
    r = run_case(case)
    assert r["result"]["outcome"] == "ROLLED_BACK"
    assert not r["leg_a_changed"] and not r["leg_b_changed"]


def test_eh05_transient_commit_retried():
    r = run_case("transient_commit")
    assert r["result"]["outcome"] == "COMMITTED_BOTH"
    assert any("retry" in t for t in r["trace"])
