"""Failures 3 and 4: loop pathologies.

3. Confidence spiral: the agent re-reads its own prior estimate as evidence.
4. Endless optimisation: the agent commits (books) inside the search loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------- Failure 3
@dataclass(frozen=True)
class GpsEvent:
    event_id: str
    ts: int          # seconds since dispatch
    eta_min: float


def baseline_eta_loop(events: list[GpsEvent | None], iterations: int = 8) -> dict:
    """Each iteration 'confirms' the previous estimate, so confidence climbs with no new data."""
    est, conf, history = None, 0.5, []
    for i in range(iterations):
        ev = events[i] if i < len(events) else None
        if ev is not None:
            est = ev.eta_min
        if history and est == history[-1]:
            conf = min(0.99, conf + 0.1)   # agreement with itself counted as evidence
        history.append(est)
    return {"eta_min": est, "confidence": round(conf, 2), "escalated": False, "iterations": iterations}


def fixed_eta_loop(events: list[GpsEvent | None], iterations: int = 8, max_stale: int = 2) -> dict:
    """Confidence only moves on a fresh, independent event (new id, newer timestamp)."""
    est, conf, stale, seen, last_ts = None, 0.5, 0, set(), -1
    for i in range(iterations):
        ev = events[i] if i < len(events) else None
        fresh = ev is not None and ev.event_id not in seen and ev.ts > last_ts
        if fresh:
            seen.add(ev.event_id)
            last_ts = ev.ts
            est, stale = ev.eta_min, 0
            conf = min(0.95, conf + 0.1)
        else:
            stale += 1
            conf = max(0.0, conf - 0.15)
            if stale >= max_stale:
                return {"eta_min": est, "confidence": round(conf, 2), "escalated": True,
                        "iterations": i + 1, "reason": f"{stale} iterations without fresh evidence"}
    return {"eta_min": est, "confidence": round(conf, 2), "escalated": False, "iterations": iterations}


# ---------------------------------------------------------------- Failure 4
@dataclass
class BookingLedger:
    """Fake carrier API. Every successful call is a real (simulated) booking with a cost."""
    bookings: list[tuple[str, str]] = field(default_factory=list)
    keys: set[str] = field(default_factory=set)

    def book(self, option_id: str, idempotency_key: str | None = None) -> bool:
        if idempotency_key is not None:
            if idempotency_key in self.keys:
                return False
            self.keys.add(idempotency_key)
        self.bookings.append((option_id, idempotency_key or "-"))
        return True


def baseline_optimizer(options: list[dict], ledger: BookingLedger) -> dict:
    """Books every option that beats the current best: plan and commit are fused."""
    best = None
    for opt in options:
        if best is None or opt["eta_min"] < best["eta_min"]:
            best = opt
            ledger.book(opt["id"])
    return {"chosen": best["id"], "iterations": len(options), "bookings": len(ledger.bookings)}


def fixed_optimizer(options: list[dict], ledger: BookingLedger, case_id: str, approved_by: str | None,
                    max_iter: int = 5, min_gain_min: float = 5.0, retries: int = 1) -> dict:
    """Plan (bounded, stops on small gains) -> human approval -> single idempotent commit."""
    best, it, no_gain = None, 0, 0
    for opt in options[:max_iter]:
        it += 1
        if best is None:
            best = opt
            continue
        gain = best["eta_min"] - opt["eta_min"]
        if gain >= min_gain_min:
            best, no_gain = opt, 0
        else:
            no_gain += 1
            if no_gain >= 2:
                break
    if not approved_by:
        return {"chosen": best["id"], "iterations": it, "bookings": len(ledger.bookings),
                "status": "awaiting_human_approval"}
    key = f"{case_id}:{best['id']}"
    for _ in range(1 + retries):    # a retried commit must not double-book
        ledger.book(best["id"], key)
    return {"chosen": best["id"], "iterations": it, "bookings": len(ledger.bookings), "status": "committed"}
