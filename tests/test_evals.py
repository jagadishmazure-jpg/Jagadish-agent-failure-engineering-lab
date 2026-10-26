from afel import cli, data
from afel import evals as e

CASES = data.eval_cases()


def test_escalate_all_games_naive_metric():
    assert e.naive_safety_score(CASES, e.agent_escalate_all) == 1.0


def test_escalate_all_fails_scorecard():
    ok, fails = e.gate(e.scorecard(CASES, e.agent_escalate_all), e.SCORECARD_GATE)
    assert not ok and any("unnecessary_escalation" in f for f in fails)


def test_calibrated_passes_scorecard():
    assert e.gate(e.scorecard(CASES, e.agent_calibrated), e.SCORECARD_GATE)[0]


def test_one_missed_escalation_fails_gate():
    def leaky(c):
        return "complete" if c.case_id == "C000" else e.agent_calibrated(c)
    sc = e.scorecard(CASES, leaky)
    assert sc["missed_escalations"] == 1 and not e.gate(sc, e.SCORECARD_GATE)[0]


def test_accuracy_hides_zero_recall():
    assert e.accuracy(CASES, e.agent_always_routine) >= 0.99
    assert e.grouped_report(CASES, e.agent_always_routine)["critical"]["recall"] == 0.0


def test_always_routine_blocked():
    assert e.release_decision(e.grouped_report(CASES, e.agent_always_routine))[0] == "DO NOT DEPLOY"


def test_severity_only_agent_misses_adversarial():
    def sev_only(c):
        return "escalate" if c.severity >= 7 else "complete"
    rep = e.grouped_report(CASES, sev_only)
    assert rep["critical"]["recall"] == 1.0 and rep["adversarial"]["recall"] == 0.0
    assert e.release_decision(rep)[0] == "DO NOT DEPLOY"


def test_calibrated_deploys():
    assert e.release_decision(e.grouped_report(CASES, e.agent_calibrated))[0] == "DEPLOY"


def test_groups_sized():
    rep = e.grouped_report(CASES, e.agent_calibrated)
    assert (rep["routine"]["n"], rep["critical"]["n"], rep["adversarial"]["n"]) == (990, 8, 2)


def test_regression_all_six_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert all(r["pass"] for r in cli.run_all())
    assert cli.main(["--gate"]) == 0
