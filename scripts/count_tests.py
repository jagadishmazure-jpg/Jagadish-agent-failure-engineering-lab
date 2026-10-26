"""Run pytest and print the real total so docs can quote it."""
import re
import subprocess
import sys


def run():
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                       capture_output=True, text=True, check=False)  # non-zero rc is reported, not raised
    tail = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", tail)) else 0
    failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", tail)) else 0
    return p.returncode, passed, failed, p.stdout

if __name__ == "__main__":
    rc, passed, failed, out = run()
    print(out[-3000:])
    print(f"TOTAL_TESTS={passed + failed} PASSED={passed} FAILED={failed}")
    sys.exit(rc)
