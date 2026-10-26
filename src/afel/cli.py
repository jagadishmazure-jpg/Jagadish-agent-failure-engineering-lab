"""Run every failure as baseline vs fixed and print a comparison. --gate exits non-zero on regression."""
from __future__ import annotations

import json
import pathlib
import sys

from . import data, evals, loops, semantic


def f1() -> dict:
    rows = data.term_messages()
    holds = [m for m, e in rows if e == "hold"]
    base_caught = sum(semantic.baseline_term_risk(m) == "hold" for m in holds)
    fixed_ok = sum(semantic.fixed_term_risk(m).action == e for m, e in rows)
    fixed_caught = sum(semantic.fixed_term_risk(m).action == "hold" for m in holds)
    base_ok = sum(semantic.baseline_term_risk(m) == e for m, e in rows)
    return {"failure": "1 term meaning", "n": len(rows),
            "baseline": f"contraindications held {base_caught}/{len(holds)}; correct {base_ok}/{len(rows)}",
            "fixed": f"contraindications held {fixed_caught}/{len(holds)}; correct {fixed_ok}/{len(rows)}",
            "pass": fixed_caught == len(holds) and base_caught < len(holds)}


def f2() -> dict:
    recs = data.ischemia_records()
    base_unsafe = sum(semantic.baseline_viability(r) == "dispatch" and not semantic.is_actually_viable(r, data.NOW)
                      for r in recs)
    dec = [semantic.fixed_viability(r, data.NOW)[0] for r in recs]
    fixed_unsafe = sum(d == "dispatch" and not semantic.is_actually_viable(r, data.NOW) for d, r in zip(dec, recs))
    esc = dec.count("escalate")
    return {"failure": "2 field direction", "n": len(recs),
            "baseline": f"unsafe dispatches {base_unsafe}/{len(recs)}",
            "fixed": f"unsafe dispatches {fixed_unsafe}/{len(recs)}; escalated {esc}",
            "pass": fixed_unsafe == 0 and base_unsafe > 0}


def f3() -> dict:
    sc = data.gps_scenarios()
    bad = [k for k in sc if k != "healthy_feed"]
    b = {k: loops.baseline_eta_loop(v) for k, v in sc.items()}
    f = {k: loops.fixed_eta_loop(v) for k, v in sc.items()}
    b_overconf = sum(b[k]["confidence"] >= 0.9 for k in bad)
    f_esc = sum(f[k]["escalated"] for k in bad)
    return {"failure": "3 confidence spiral", "n": len(sc),
            "baseline": f"stale feeds ending >=0.90 confidence {b_overconf}/{len(bad)}; escalated 0",
            "fixed": f"stale feeds escalated {f_esc}/{len(bad)}; healthy escalated "
                     f"{int(f['healthy_feed']['escalated'])}",
            "pass": f_esc == len(bad) and not f["healthy_feed"]["escalated"] and b_overconf > 0}


def f4() -> dict:
    opts = data.transport_options()
    bl, fl, pl = loops.BookingLedger(), loops.BookingLedger(), loops.BookingLedger()
    b = loops.baseline_optimizer(opts, bl)
    pending = loops.fixed_optimizer(opts, pl, "CASE-1", approved_by=None)
    f = loops.fixed_optimizer(opts, fl, "CASE-1", approved_by="dispatcher-on-call")
    loops.fixed_optimizer(opts, fl, "CASE-1", approved_by="dispatcher-on-call")  # replayed request
    return {"failure": "4 endless optimisation", "n": len(opts),
            "baseline": f"bookings {b['bookings']}; iterations {b['iterations']}",
            "fixed": f"bookings {len(fl.bookings)} (after retry + replay); iterations {f['iterations']}; "
                     f"without approval bookings {len(pl.bookings)} ({pending['status']})",
            "pass": len(fl.bookings) == 1 and len(pl.bookings) == 0 and b["bookings"] > 1}


def f5() -> dict:
    cases = data.eval_cases()
    naive = evals.naive_safety_score(cases, evals.agent_escalate_all)
    sc_all = evals.scorecard(cases, evals.agent_escalate_all)
    sc_cal = evals.scorecard(cases, evals.agent_calibrated)
    ok_all, fails_all = evals.gate(sc_all, evals.SCORECARD_GATE)
    ok_cal, _ = evals.gate(sc_cal, evals.SCORECARD_GATE)
    return {"failure": "5 escalate-everything", "n": len(cases),
            "baseline": f"escalate-all naive safety score {naive}; scorecard gate {'PASS' if ok_all else 'FAIL'} "
                        f"({'; '.join(fails_all)})",
            "fixed": f"calibrated agent scorecard {sc_cal}; gate {'PASS' if ok_cal else 'FAIL'}",
            "pass": naive == 1.0 and not ok_all and ok_cal}


def f6() -> dict:
    cases = data.eval_cases()
    acc = evals.accuracy(cases, evals.agent_always_routine)
    rep_b = evals.grouped_report(cases, evals.agent_always_routine)
    dec_b, _ = evals.release_decision(rep_b)
    rep_f = evals.grouped_report(cases, evals.agent_calibrated)
    dec_f, _ = evals.release_decision(rep_f)
    return {"failure": "6 accuracy hides misses", "n": len(cases),
            "baseline": f"always-routine accuracy {acc}; critical recall {rep_b['critical']['recall']}; "
                        f"release {dec_b}",
            "fixed": f"calibrated accuracy {evals.accuracy(cases, evals.agent_calibrated)}; critical recall "
                     f"{rep_f['critical']['recall']}; adversarial recall {rep_f['adversarial']['recall']}; "
                     f"release {dec_f}",
            "pass": acc >= 0.99 and dec_b == "DO NOT DEPLOY" and dec_f == "DEPLOY"}


def run_all() -> list[dict]:
    return [f1(), f2(), f3(), f4(), f5(), f6()]


def main(argv: list[str]) -> int:
    rows = run_all()
    for r in rows:
        print(f"[{'PASS' if r['pass'] else 'FAIL'}] Failure {r['failure']} (n={r['n']}, synthetic)")
        print(f"    baseline: {r['baseline']}")
        print(f"    fixed:    {r['fixed']}")
    out = pathlib.Path("results")
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps({"label": "measured on synthetic data", "rows": rows}, indent=2))
    if "--gate" in argv and not all(r["pass"] for r in rows):
        print("RELEASE GATE: DO NOT DEPLOY")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
