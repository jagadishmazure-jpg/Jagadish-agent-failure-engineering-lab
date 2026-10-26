"""Fail if any word / bigram in tracked text matches a hashed blocklist of real company names."""
import hashlib
import pathlib
import re
import sys
from itertools import pairwise

ROOT = pathlib.Path(__file__).resolve().parents[1]
HASHES = set((ROOT / "scripts" / "brand_blocklist.sha256").read_text().split())
SKIP = {"third_party", ".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv"}
hits = []
for p in ROOT.rglob("*"):
    if p.is_dir() or SKIP & set(p.parts) or p.suffix not in {".py", ".md", ".json", ".yml", ".yaml", ".xml", ".txt", ".jsonl"}:
        continue
    words = re.findall(r"[a-z0-9]+", p.read_text(errors="ignore").lower())
    grams = set(words) | {a + " " + b for a, b in pairwise(words)}
    for g in grams:
        if hashlib.sha256(g.encode()).hexdigest() in HASHES:
            hits.append(str(p.relative_to(ROOT)))
if hits:
    sys.exit(f"brand-name check failed in: {sorted(set(hits))}")
print("brand-name check passed")
