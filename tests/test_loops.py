import pytest

from afel import data
from afel import loops as l

SC = data.gps_scenarios()


@pytest.mark.parametrize("name", ["gps_dark_after_1", "replayed_event", "out_of_order"])
def test_stale_feeds_escalate(name):
    r = l.fixed_eta_loop(SC[name])
    assert r["escalated"] and r["confidence"] < 0.9


@pytest.mark.parametrize("name", ["gps_dark_after_1", "replayed_event"])
def test_baseline_spirals(name):
    assert l.baseline_eta_loop(SC[name])["confidence"] >= 0.9


def test_healthy_feed_no_escalation():
    r = l.fixed_eta_loop(SC["healthy_feed"])
    assert not r["escalated"] and r["eta_min"] == SC["healthy_feed"][-1].eta_min


def test_escalates_after_exactly_two_stale():
    assert l.fixed_eta_loop(SC["gps_dark_after_1"])["iterations"] == 3


def test_loop_is_deterministic():
    assert l.fixed_eta_loop(SC["out_of_order"]) == l.fixed_eta_loop(SC["out_of_order"])


OPTS = data.transport_options()


def test_baseline_books_many():
    led = l.BookingLedger()
    l.baseline_optimizer(OPTS, led)
    assert len(led.bookings) > 1


def test_no_commit_without_human():
    led = l.BookingLedger()
    r = l.fixed_optimizer(OPTS, led, "C1", approved_by=None)
    assert r["status"] == "awaiting_human_approval" and not led.bookings


def test_single_commit_with_retry_and_replay():
    led = l.BookingLedger()
    for _ in range(3):
        l.fixed_optimizer(OPTS, led, "C1", approved_by="dispatcher")
    assert len(led.bookings) == 1


def test_max_iterations_bounded():
    many = [{"id": f"O{i}", "eta_min": 500 - 50 * i} for i in range(9)]
    assert l.fixed_optimizer(many, l.BookingLedger(), "C2", None, max_iter=4)["iterations"] == 4


def test_small_gains_stop_search():
    flat = [{"id": f"O{i}", "eta_min": 100 - i} for i in range(10)]
    assert l.fixed_optimizer(flat, l.BookingLedger(), "C3", None)["iterations"] == 3


def test_big_gain_accepted():
    opts = [{"id": "A", "eta_min": 200}, {"id": "B", "eta_min": 120}]
    assert l.fixed_optimizer(opts, l.BookingLedger(), "C4", None)["chosen"] == "B"
