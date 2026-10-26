"""Failures 1 and 2: semantic misreads of domain terms and field meanings.

Domain: a fictional time-critical medical logistics network ("Northbridge Transit Network").
Tolerance values are illustrative lab constants, NOT clinical guidance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

# ---------------------------------------------------------------- Failure 1: term meaning
POSITIVE_WORDS = {"positive", "good", "clear", "stable", "ok", "pass", "passed"}
NEGATIVE_WORDS = {"negative", "bad", "fail", "failed", "delay", "risk", "rejected"}


def baseline_term_risk(text: str) -> str:
    """Naive: generic sentiment. 'positive' reads as good news."""
    words = re.findall(r"[a-z]+", text.lower())
    score = sum(w in POSITIVE_WORDS for w in words) - sum(w in NEGATIVE_WORDS for w in words)
    return "proceed" if score >= 0 else "hold"


# Synonym table -> canonical concept id (a tiny lab ontology, not a real terminology).
SYNONYMS = {
    "positive crossmatch": "XM_POS", "crossmatch positive": "XM_POS", "xm positive": "XM_POS",
    "xm+": "XM_POS", "+ve crossmatch": "XM_POS", "positive xm": "XM_POS",
    "negative crossmatch": "XM_NEG", "crossmatch negative": "XM_NEG", "xm negative": "XM_NEG",
    "xm-": "XM_NEG", "negative xm": "XM_NEG", "-ve crossmatch": "XM_NEG",
    "positive serology": "SERO_POS", "serology positive": "SERO_POS",
    "negative serology": "SERO_NEG", "serology negative": "SERO_NEG",
}
# concept -> policy status. Positive tests here are contraindications: the opposite of sentiment.
ONTOLOGY = {
    "XM_POS": "contraindication", "XM_NEG": "compatible",
    "SERO_POS": "contraindication", "SERO_NEG": "compatible",
}


def normalize(text: str) -> str:
    t = re.sub(r"[^a-z0-9+\- ]", " ", text.lower())
    return re.sub(r"\s+", " ", t).strip()


@dataclass(frozen=True)
class TermDecision:
    action: str          # proceed | hold | expert_review
    concepts: tuple[str, ...]
    reason: str


def fixed_term_risk(text: str) -> TermDecision:
    """Normalize -> concept lookup -> policy status. Unknown clinical-looking terms go to an expert."""
    t = normalize(text)
    found = tuple(sorted({cid for phrase, cid in SYNONYMS.items() if phrase in t}))
    statuses = {ONTOLOGY[c] for c in found}
    if "contraindication" in statuses:
        return TermDecision("hold", found, "policy: contraindication concept present")
    if found and statuses == {"compatible"}:
        return TermDecision("proceed", found, "all concepts compatible")
    if any(k in t for k in ("crossmatch", "xm", "serology", "antibod", "hla")):
        return TermDecision("expert_review", found, "clinical term not in ontology")
    return TermDecision("proceed", found, "no clinical concepts")


# ---------------------------------------------------------------- Failure 2: field meaning
@dataclass(frozen=True)
class FieldDef:
    name: str
    direction: str      # "elapsed" or "remaining"
    unit: str           # "h" or "min"
    origin: str         # which timestamp the clock started at


FIELD_DEFS = {
    "cold_ischemia": FieldDef("cold_ischemia", "elapsed", "h", "cross_clamp_ts"),
}
# Illustrative lab tolerances (hours) per fictional package class. NOT clinical values.
MAX_TOLERANCE_H = {"class_a": 6.0, "class_b": 12.0, "class_c": 24.0}
SAFETY_MARGIN_H = 1.0


def baseline_viability(record: dict) -> str:
    """Naive: reads the number as hours REMAINING and compares to transit time."""
    return "dispatch" if record["cold_ischemia"] >= record["transit_h"] else "decline"


def _hours(value: float, unit: str) -> float:
    if unit == "h":
        return value
    if unit == "min":
        return value / 60.0
    raise ValueError(unit)


def fixed_viability(record: dict, now: datetime) -> tuple[str, float | None, str]:
    """Use the field definition; recompute elapsed from timestamps; escalate when unsure.

    Returns (decision, remaining_hours_or_None, reason)."""
    fd = FIELD_DEFS.get("cold_ischemia")
    unit = record.get("unit")
    if fd is None or unit not in ("h", "min") or record.get("package_class") not in MAX_TOLERANCE_H:
        return "escalate", None, "missing field definition, unit or class"
    elapsed = _hours(record["cold_ischemia"], unit) if fd.direction == "elapsed" else None
    origin = record.get(fd.origin)
    if origin:
        computed = (now - datetime.fromisoformat(origin)).total_seconds() / 3600
        if elapsed is not None and abs(computed - elapsed) > 0.5:
            return "escalate", None, f"reported {elapsed:.1f}h disagrees with timestamps {computed:.1f}h"
        elapsed = computed
    if elapsed is None:
        return "escalate", None, "cannot derive elapsed time"
    remaining = MAX_TOLERANCE_H[record["package_class"]] - elapsed
    if remaining - record["transit_h"] >= SAFETY_MARGIN_H:
        return "dispatch", round(remaining, 2), "fits with margin"
    if remaining - record["transit_h"] >= 0:
        return "escalate", round(remaining, 2), "inside safety margin"
    return "decline", round(remaining, 2), "would exceed tolerance"


def is_actually_viable(record: dict, now: datetime) -> bool:
    """Ground truth from the generator: true elapsed is always derivable from cross_clamp_ts."""
    elapsed = (now - datetime.fromisoformat(record["true_cross_clamp_ts"])).total_seconds() / 3600
    return MAX_TOLERANCE_H[record["package_class"]] - elapsed >= record["transit_h"]
