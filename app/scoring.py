"""Independent fixture-scoring utility; NEVER passed into inference prompts."""
from __future__ import annotations

import json
from pathlib import Path


def score(report: dict, truth_path: Path) -> dict:
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    expected = set(truth["expected"])
    found = {str(x.get("invoice_ref", "")) for x in report.get("findings", []) if isinstance(x, dict)}
    hits = sorted(expected & found)
    missed = sorted(expected - found)
    false_positives = sorted(found - expected)
    denominator = len(expected)
    return {"planted": denominator, "found": len(hits), "recall": round(len(hits) / denominator, 4) if denominator else 0, "missed": missed, "false_positives": false_positives, "passes_quality_gate": len(hits) >= 14 and not false_positives}
