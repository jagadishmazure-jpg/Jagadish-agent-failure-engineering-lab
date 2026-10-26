"""Regenerate the README results block from a real run (results/*.json + live pytest count).

--check fails if the committed README differs from what a fresh run produces."""
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from count_tests import run

ROOT = pathlib.Path(__file__).resolve().parents[1]
BEGIN, END = "<!-- BEGIN GENERATED -->", "<!-- END GENERATED -->"

def block():
    env = {**os.environ, "PYTHONPATH": "src"}
    subprocess.run([sys.executable, "-m", "afel.cli"], cwd=ROOT, check=True, capture_output=True, env=env)
    rc, passed, _failed, _ = run()
    if rc != 0:
        sys.exit("tests failed")
    res = json.loads((ROOT / "results" / "results.json").read_text())
    lines = [BEGIN, "", f"**Tests:** {passed} passing (`python scripts/count_tests.py`).", "",
             f"**Comparison** ({res['label']}; `PYTHONPATH=src python -m afel.cli`):", "",
             "| Failure | n | Naive baseline | Fixed | Gate |", "|---|---|---|---|---|"]
    for r in res["rows"]:
        lines.append(f"| {r['failure']} | {r['n']} | {r['baseline']} | {r['fixed']} | {'PASS' if r['pass'] else 'FAIL'} |")
    lines += ["", END]
    return "\n".join(lines)

if __name__ == "__main__":
    readme = ROOT / "README.md"
    txt = readme.read_text()
    a, b = txt.index(BEGIN), txt.index(END) + len(END)
    new = txt[:a] + block() + txt[b:]
    if "--check" in sys.argv:
        if new != txt:
            sys.exit("README results block is stale: run python scripts/render_readme.py")
        print("README results block matches a fresh run")
    else:
        readme.write_text(new)
        print("README updated")
