import csv
import json
from pathlib import Path

from tools.generate_fixture import generate
from app.scoring import score
from app.main import _source_security_findings, _check_evidence


def test_fixture_has_15_distinct_planted_anomalies(tmp_path: Path):
    truth = generate(tmp_path)
    assert truth["count"] == 15
    assert len(truth["expected"]) == 15
    with (tmp_path / "invoices.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) >= 30
    assert any(r["Bill Number"] == "INV-1021B" for r in rows)
    assert all((tmp_path / filename).exists() for filename in ("purchase_orders.csv", "goods_receipts.csv", "invoices.csv"))


def test_scoring_exact_gate(tmp_path: Path):
    truth = generate(tmp_path)
    perfect = {"findings": [{"invoice_ref": ref} for ref in truth["expected"]]}
    assert score(perfect, tmp_path.parent / (tmp_path.name + "_truth") / "ground_truth.json")["passes_quality_gate"]
    one_missed = {"findings": perfect["findings"][:-1]}
    assert score(one_missed, tmp_path.parent / (tmp_path.name + "_truth") / "ground_truth.json")["passes_quality_gate"]
    two_missed = {"findings": perfect["findings"][:-2]}
    assert not score(two_missed, tmp_path.parent / (tmp_path.name + "_truth") / "ground_truth.json")["passes_quality_gate"]
    false_alarm = {"findings": perfect["findings"] + [{"invoice_ref": "INV-1016"}]}
    assert not score(false_alarm, tmp_path.parent / (tmp_path.name + "_truth") / "ground_truth.json")["passes_quality_gate"]


def test_hostile_invoice_note_does_not_run(tmp_path: Path):
    generate(tmp_path)
    findings = _source_security_findings(tmp_path / "invoices.csv")
    assert [finding["invoice_ref"] for finding in findings] == ["INV-1015"]


def test_source_reference_must_exist(tmp_path: Path):
    generate(tmp_path)
    import pytest
    from app.sandbox import SandboxError
    with pytest.raises(SandboxError, match="Ungrounded"):
        _check_evidence({"findings": [{"invoice_ref": "FAKE", "reason": "Invalid", "evidence": ["invoices.csv:2"]}]}, tmp_path)


def test_cited_invoice_row_is_checked(tmp_path: Path):
    generate(tmp_path)
    from app.sandbox import SandboxError
    import pytest
    with pytest.raises(SandboxError, match="Ungrounded"):
        _check_evidence({"findings": [{"invoice_ref": "INV-1028", "reason": "Sample", "evidence": ["invoices.csv:2"]}]}, tmp_path)

def test_valid_invoice_citation_and_hostile_security_note(tmp_path: Path):
    generate(tmp_path)
    result = _check_evidence({"findings": [{"invoice_ref": "INV-1001", "reason": "Mismatch", "evidence": ["invoices.csv:2", "purchase_orders.csv:2"]}]}, tmp_path)
    assert any(f["invoice_ref"] == "INV-1001" for f in result["findings"])
    assert any(f["invoice_ref"] == "INV-1015" for f in result["findings"])
