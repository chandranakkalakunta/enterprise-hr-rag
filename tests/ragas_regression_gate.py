"""
RAGAS Regression Gate — CI/CD quality gate.
Reads the latest evaluation_results.json and fails the build
if scores fall below thresholds defined in env vars / common.env.

Run: python tests/ragas_regression_gate.py
Exits 0 if scores pass, 1 if any threshold is breached.
"""
import json
import os
import sys

RESULTS_FILE = "data/ground_truth/evaluation_results.json"

THRESHOLD_RELEVANCY = float(os.environ.get("RAGAS_RELEVANCY_THRESHOLD", "0.80"))
THRESHOLD_SOURCE    = float(os.environ.get("RAGAS_PRECISION_THRESHOLD", "0.75"))


def main():
    if not os.path.exists(RESULTS_FILE):
        print(f"[SKIP] {RESULTS_FILE} not found — skipping regression gate")
        sys.exit(0)

    with open(RESULTS_FILE) as f:
        data = json.load(f)

    summary = data.get("summary", {})
    avg_relevancy   = summary.get("avg_relevancy", 0)
    source_accuracy = summary.get("source_accuracy", 0)
    alpha           = data.get("alpha", "?")
    model           = data.get("model", "?")

    print("\n" + "=" * 50)
    print("RAGAS Regression Gate")
    print("=" * 50)
    print(f"  Model:          {model}")
    print(f"  Alpha:          {alpha}")
    print(f"  Avg Relevancy:  {avg_relevancy:.3f}  (threshold: {THRESHOLD_RELEVANCY})")
    print(f"  Source Accuracy:{source_accuracy:.3f}  (threshold: {THRESHOLD_SOURCE})")
    print("=" * 50)

    failures = []
    if avg_relevancy < THRESHOLD_RELEVANCY:
        failures.append(
            f"avg_relevancy {avg_relevancy:.3f} < threshold {THRESHOLD_RELEVANCY}"
        )
    if source_accuracy < THRESHOLD_SOURCE:
        failures.append(
            f"source_accuracy {source_accuracy:.3f} < threshold {THRESHOLD_SOURCE}"
        )

    if failures:
        print("\n[FAIL] Quality gate breached:")
        for f in failures:
            print(f"  ✗  {f}")
        sys.exit(1)
    else:
        print("\n[PASS] All quality gates passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
