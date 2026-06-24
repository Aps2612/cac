"""Unit tests for the pure decision logic (no database needed).

Run:  python -m pytest          (or: python -m pytest -v)
"""

from cac.cohort import cohort_of
from cac.measure import base_prob, lift


def test_prospect_is_not_targeted():
    assert cohort_of(0, None, 0, 100) is None


def test_cohort_ladder_first_match_wins():
    assert cohort_of(5, 10, 500, 300) == "loyal_regular"
    assert cohort_of(4, 90, 600, 300) == "lapsing_vip"
    assert cohort_of(1, 30, 50, 300) == "at_risk_first_timer"
    # One order, 200 days: matches one_and_done BEFORE the dormant rule -> first match wins.
    assert cohort_of(1, 200, 50, 300) == "one_and_done"
    assert cohort_of(2, 120, 100, 300) == "repeat_winback"
    assert cohort_of(2, 300, 50, 300) == "dormant_winback"


def test_lift_is_positive_and_significant():
    m = lift(t_n=1000, t_c=200, c_n=1000, c_c=100)   # 20% vs 10%
    assert round(m["abs_lift"], 2) == 0.10
    assert m["p_value"] < 0.001


def test_lift_handles_empty_control():
    m = lift(t_n=10, t_c=3, c_n=0, c_c=0)
    assert m["ctrl_rate"] == 0.0
    assert m["p_value"] == 1.0


def test_base_prob_stays_in_bounds():
    assert 0.02 <= base_prob(0, 0.6) <= 0.30
    assert 0.02 <= base_prob(10_000, 0.0) <= 0.30
