from __future__ import annotations

import argparse
import json
from pathlib import Path
from app.scoring import score

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.response.read_text(encoding="utf-8"))
    report = result.get("report", result)
    evaluation = score(report, args.truth)
    elapsed = result.get("elapsed_seconds")
    corrections = result.get("attempts", 999) - 1
    evaluation["elapsed_seconds"] = elapsed
    evaluation["corrections"] = corrections
    evaluation["passes_all_measurements"] = evaluation["passes_quality_gate"] and isinstance(elapsed, (float, int)) and elapsed < 180 and corrections <= 3
    print(json.dumps(evaluation, indent=2))
