"""
run_10_iterations.py — Rigorous 10-Iteration Stability & Determinism Stress Test
"""

import sys
import subprocess
import time
import hashlib
from pathlib import Path

PYTHON_EXE = sys.executable
SCRIPT_DIR = Path(__file__).resolve().parent
REPRODUCE_SCRIPT = SCRIPT_DIR / "reproduce_bug.py"
DEEP_TEST_SCRIPT = SCRIPT_DIR / "test_deduplication_deep.py"
RESULTS_FILE = SCRIPT_DIR / "reproduction_results.json"

def run_stress_test(iterations=10):
    print("=" * 80)
    print(f"RUNNING {iterations}-ITERATION STABILITY, FLAKINESS & DETERMINISM SUITE")
    print(f"Python:    {PYTHON_EXE}")
    print(f"Workspace: {SCRIPT_DIR}")
    print("=" * 80)

    stats = []
    previous_hash = None

    for i in range(1, iterations + 1):
        t0 = time.perf_counter()

        # 1. Run reproduce_bug.py
        p1 = subprocess.run(
            [PYTHON_EXE, str(REPRODUCE_SCRIPT)],
            capture_output=True,
            text=True
        )
        t_repro = time.perf_counter() - t0

        # Check results file hash
        if RESULTS_FILE.exists():
            content_hash = hashlib.sha256(RESULTS_FILE.read_bytes()).hexdigest()[:12]
        else:
            content_hash = "MISSING"

        # Check determinism with previous iteration
        hash_matched = (previous_hash is None or content_hash == previous_hash)
        previous_hash = content_hash

        # 2. Run test_deduplication_deep.py
        t1 = time.perf_counter()
        p2 = subprocess.run(
            [PYTHON_EXE, str(DEEP_TEST_SCRIPT)],
            capture_output=True,
            text=True
        )
        t_deep = time.perf_counter() - t1
        t_total = time.perf_counter() - t0

        passed = (p1.returncode == 0 and p2.returncode == 0 and hash_matched)
        stats.append({
            "iteration": i,
            "repro_code": p1.returncode,
            "deep_code": p2.returncode,
            "hash": content_hash,
            "repro_time_ms": round(t_repro * 1000, 1),
            "deep_time_ms": round(t_deep * 1000, 1),
            "total_time_ms": round(t_total * 1000, 1),
            "status": "PASS" if passed else "FAIL",
            "p1_err": p1.stderr if p1.returncode != 0 else "",
            "p2_err": p2.stderr if p2.returncode != 0 else "",
        })

        status_str = "PASS" if passed else "FAIL"
        print(f"Iteration {i:2d}/{iterations}: {status_str} | "
              f"reproduce_bug: {p1.returncode} ({t_repro*1000:5.1f}ms) | "
              f"deep_test: {p2.returncode} ({t_deep*1000:5.1f}ms) | "
              f"hash: {content_hash} | total: {t_total*1000:5.1f}ms")

    print("\n" + "=" * 80)
    print("10-ITERATION STABILITY SUMMARY:")
    print("=" * 80)
    passed_runs = sum(1 for s in stats if s["status"] == "PASS")
    avg_total = sum(s["total_time_ms"] for s in stats) / len(stats)
    hashes = set(s["hash"] for s in stats)

    print(f"Total Successful Runs:  {passed_runs}/{iterations} ({passed_runs/iterations*100:.1f}%)")
    print(f"Average Execution Time: {avg_total:.1f}ms per iteration")
    print(f"Output Hash Uniformity: {len(hashes)} unique hash across {iterations} runs ({list(hashes)[0]})")

    if passed_runs == iterations and len(hashes) == 1:
        print("\n>>> VERDICT: ZERO FLAKINESS, 100% DETERMINISTIC ACROSS ALL 10 RUNS <<<")
        return 0
    else:
        print("\n>>> VERDICT: ISSUES DETECTED IN STABILITY TEST <<<")
        for s in stats:
            if s["status"] != "PASS":
                print(f"Iteration {s['iteration']} failed: repro={s['repro_code']}, deep={s['deep_code']}")
                if s["p1_err"]: print(f"  Repro Error: {s['p1_err']}")
                if s["p2_err"]: print(f"  Deep Error:  {s['p2_err']}")
        return 1

if __name__ == "__main__":
    sys.exit(run_stress_test(10))
