"""Deterministic synthetic datasets (seeded). Fictional network, fictional sites, no real patients."""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from .evals import Case
from .loops import GpsEvent

NOW = datetime(2026, 1, 15, 12, 0, 0)
SITES = ["Northbridge Hub", "Elmfield Center", "Copper Lake Unit", "Ashgrove Station", "Redstone Point"]


def term_messages(seed: int = 7) -> list[tuple[str, str]]:
    """(message, expected_action). Expected is hold for contraindications, review for unknown terms."""
    rng = random.Random(seed)
    hold = ["Positive crossmatch reported, good news, team ready", "XM positive on final panel, all stable",
            "Lab says +ve crossmatch, results clear", "Serology positive, courier passed checkpoint",
            "Crossmatch positive. Transport is ok", "Positive XM on repeat test, looking good"]
    proceed = ["Negative crossmatch, courier delayed by traffic", "XM negative, minor delay at gate",
               "Serology negative; weather risk on route", "Negative xm confirmed, failed first pickup slot",
               "Package sealed, courier on time"]
    review = ["Virtual crossmatch borderline, awaiting HLA panel", "Donor-specific antibody weak signal, ok"]
    rows = [(m, "hold") for m in hold] + [(m, "proceed") for m in proceed] + [(m, "expert_review") for m in review]
    rng.shuffle(rows)
    return rows


def ischemia_records(n: int = 40, seed: int = 11) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        cls = rng.choice(["class_a", "class_b", "class_c"])
        elapsed = round(rng.uniform(0.5, 20.0), 1)
        clamp = NOW - timedelta(hours=elapsed)
        rec = {"id": f"PKG-{i:03d}", "package_class": cls, "cold_ischemia": elapsed, "unit": "h",
               "transit_h": round(rng.uniform(0.5, 6.0), 1), "cross_clamp_ts": clamp.isoformat(),
               "true_cross_clamp_ts": clamp.isoformat(), "origin_site": rng.choice(SITES)}
        r = rng.random()
        if r < 0.1:
            rec["unit"] = None                          # missing unit
        elif r < 0.2:
            rec["cold_ischemia"] = round(elapsed * 60)  # reported in minutes
            rec["unit"] = "min"
        elif r < 0.25:
            rec["cross_clamp_ts"] = None                # no timestamp, rely on definition
        out.append(rec)
    return out


def gps_scenarios() -> dict[str, list[GpsEvent | None]]:
    """Named event streams. None = no new GPS fix that iteration; repeats replay the same event."""
    a = GpsEvent("gps-001", 60, 95.0)
    return {
        "healthy_feed": [GpsEvent(f"gps-{i:03d}", 60 * (i + 1), 95.0 - 8 * i) for i in range(8)],
        "gps_dark_after_1": [a] + [None] * 7,
        "replayed_event": [a, a, a, a, a, a, a, a],
        "out_of_order": [GpsEvent("gps-005", 300, 60.0), GpsEvent("gps-004", 240, 70.0), None, None],
    }


def transport_options(seed: int = 5, n: int = 12) -> list[dict]:
    """Options arrive best-ish last so a greedy 'book on improvement' loop books many times."""
    rng = random.Random(seed)
    etas = sorted((round(rng.uniform(80, 240), 1) for _ in range(n)), reverse=True)
    modes = ["ground", "charter", "air-ambulance", "rail-courier"]
    return [{"id": f"OPT-{i:02d}", "mode": rng.choice(modes), "eta_min": e} for i, e in enumerate(etas)]


def eval_cases(seed: int = 3, n_routine: int = 990, n_critical: int = 8, n_adversarial: int = 2) -> list[Case]:
    """Imbalanced on purpose: ~99% routine, so accuracy alone looks excellent."""
    rng = random.Random(seed)
    cases = []
    for i in range(n_routine):
        cases.append(Case(f"R{i:04d}", "routine", rng.randint(0, 5), ("on_time",), False))
    crit = sorted(("xm_pos", "tolerance_breach", "gps_dark", "temp_excursion"))
    for i in range(n_critical):
        cases.append(Case(f"C{i:03d}", "critical", rng.randint(7, 10), (crit[i % len(crit)],), True))
    for i in range(n_adversarial):  # low severity score hides a critical signal
        cases.append(Case(f"A{i:03d}", "adversarial", 1, ("on_time", "seal_broken"), True))
    return cases
