import pytest

from afel import data
from afel import semantic as s


@pytest.mark.parametrize("msg", ["Positive crossmatch, good news", "XM positive", "lab: +ve crossmatch",
                                 "crossmatch positive!", "Serology positive, all clear", "positive xm"])
def test_contraindications_held(msg):
    assert s.fixed_term_risk(msg).action == "hold"


@pytest.mark.parametrize("msg", ["Positive crossmatch, good news", "XM positive, stable"])
def test_baseline_misreads_positive(msg):
    assert s.baseline_term_risk(msg) == "proceed"   # known failure kept visible


def test_negative_crossmatch_proceeds_despite_negative_words():
    assert s.fixed_term_risk("Negative crossmatch, courier delayed").action == "proceed"


def test_unknown_clinical_term_goes_to_expert():
    assert s.fixed_term_risk("HLA antibody panel borderline").action == "expert_review"


def test_mixed_concepts_hold_wins():
    assert s.fixed_term_risk("negative serology but positive crossmatch").action == "hold"


def test_all_dataset_rows_correct():
    assert all(s.fixed_term_risk(m).action == e for m, e in data.term_messages())


def _rec(**kw):
    base = {"package_class": "class_b", "cold_ischemia": 10.0, "unit": "h", "transit_h": 4.0,
            "cross_clamp_ts": None}
    base.update(kw)
    return base


def test_14h_is_elapsed_not_remaining():
    r = _rec(cold_ischemia=14.0, transit_h=3.0)
    assert s.baseline_viability(r) == "dispatch"
    assert s.fixed_viability(r, data.NOW)[0] == "decline"


def test_minutes_converted():
    assert s.fixed_viability(_rec(cold_ischemia=120, unit="min", transit_h=2.0), data.NOW)[1] == 10.0


def test_missing_unit_escalates():
    assert s.fixed_viability(_rec(unit=None), data.NOW)[0] == "escalate"


def test_unknown_class_escalates():
    assert s.fixed_viability(_rec(package_class="class_z"), data.NOW)[0] == "escalate"


def test_inside_margin_escalates():
    assert s.fixed_viability(_rec(cold_ischemia=7.5, transit_h=4.0), data.NOW)[0] == "escalate"


def test_timestamp_disagreement_escalates():
    from datetime import timedelta
    ts = (data.NOW - timedelta(hours=9)).isoformat()
    assert s.fixed_viability(_rec(cold_ischemia=3.0, cross_clamp_ts=ts), data.NOW)[0] == "escalate"


def test_timestamp_used_when_present():
    from datetime import timedelta
    ts = (data.NOW - timedelta(hours=3)).isoformat()
    d, rem, _ = s.fixed_viability(_rec(cold_ischemia=3.0, cross_clamp_ts=ts), data.NOW)
    assert d == "dispatch" and rem == 9.0


def test_fixed_never_unsafe_on_dataset():
    for r in data.ischemia_records(200, seed=99):
        if s.fixed_viability(r, data.NOW)[0] == "dispatch":
            assert s.is_actually_viable(r, data.NOW)
