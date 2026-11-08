"""Stage 2 local-only regression and failure-mode tests.

External model and Docker calls are always mocked. These tests do NOT
constitute evidence of live inference, actual sandboxing, or deployment.
"""
from __future__ import annotations

import csv
import json
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import inference, sandbox
from app.main import _check_evidence, _source_security_findings, app
from tools.generate_fixture import generate


def uploads(po=b"A,B\nx,y\n", receipt=b"A,B\nx,y\n", invoice=b"Bill Number,Notes\nINV-1,ok\n"):
    return {
        "purchase_orders": ("orders.csv", po, "text/csv"),
        "goods_receipts": ("receipts.csv", receipt, "text/csv"),
        "invoices": ("invoices.csv", invoice, "text/csv"),
    }


@pytest.mark.parametrize("bad,expected", [
    (b"A,A\n1,2\n", "Duplicate CSV headers"),
    (b"A,B\n1,2,3\n", "extra unlabelled columns"),
    (b"A,B\n1,\x00\n", "NUL bytes"),
    (b"A,B\n", "no records"),
    (b"A,B\n\"unterminated,2\n", "Invalid CSV"),
])
def test_rejects_broken_upload_without_invoking_agent(monkeypatch, enabled_api, bad, expected):
    response = TestClient(app).post("/api/analyse", files=uploads(po=bad), headers=enabled_api)
    assert response.status_code == 422
    assert expected in response.json()["detail"]


def test_rejects_oversized_upload_without_invoking_agent(monkeypatch, enabled_api):
    r = TestClient(app).post("/api/analyse", files=uploads(po=b"A,B\n"+b"a,"+b"b"*300_000), headers=enabled_api)
    assert r.status_code == 413


def test_bad_invoice_reference_inside_note_is_not_valid_evidence(tmp_path):
    generate(tmp_path)
    path = tmp_path / "invoices.csv"
    with path.open(newline="", encoding="utf-8") as h:
        rows = list(csv.DictReader(h))
        cols = list(rows[0])
    rows[1]["Supplier Note"] = "INV-1001 mentioned here, not the actual invoice ID"
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, cols)
        w.writeheader(); w.writerows(rows)
    with pytest.raises(sandbox.SandboxError, match="Ungrounded"):
        _check_evidence({"findings": [{"invoice_ref": "INV-1001", "kind": "suspicious", "reason": "Reference mentioned", "evidence": ["invoices.csv:3"]}]},tmp_path)


def test_physical_row_numbers_handle_embedded_newlines(tmp_path):
    generate(tmp_path)
    path = tmp_path / "invoices.csv"
    with path.open(newline="", encoding="utf-8") as h:
        rows = list(csv.DictReader(h)); cols = list(rows[0])
    rows[0]["Supplier Note"] = "Routine line one\nRoutine line two"
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, cols)
        w.writeheader(); w.writerows(rows)
    with path.open(newline="", encoding="utf-8") as h:
        reader = csv.DictReader(h)
        positions = {r["Bill Number"]: reader.line_num for r in reader}
    assert positions["INV-1002"] == 4
    report = {"findings": [{"invoice_ref":"INV-1002", "kind":"supplier_identity", "reason":"Ambiguous vendor", "evidence":["invoices.csv:4"]}]}
    validated = _check_evidence(report,tmp_path)
    assert any(f["invoice_ref"]=="INV-1002" for f in validated["findings"])
    with pytest.raises(sandbox.SandboxError, match="Ungrounded"):
        _check_evidence({"findings": [{"invoice_ref":"INV-1002", "kind":"supplier_identity", "reason":"Bad citation", "evidence":["invoices.csv:3"]}]},tmp_path)
    assert _source_security_findings(path)[0]["evidence"][0] == f'invoices.csv:{positions["INV-1015"]}'


def test_invalid_model_report_is_retried_through_evidence_validator(monkeypatch, tmp_path):
    generate(tmp_path)
    monkeypatch.setenv("VULTR_INFERENCE_API_KEY", "TEST_ONLY")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_: object()))
    monkeypatch.setattr(inference, "ask_model", lambda *_: ("print('test')", "deepseek-v4.1-flash-1017"))
    inv = [
        {"findings": [{"invoice_ref":"FAKE", "kind":"test", "reason":"No actual row", "evidence":["invoices.csv:2"]}], "analysed_invoices":32},
        {"findings": [{"invoice_ref":"INV-1001", "kind":"supplier_mismatch", "reason":"Mismatched supplier", "evidence":["invoices.csv:2"]}], "analysed_invoices":32},
    ]
    calls = []
    def fake_docker(*_):
        calls.append(1)
        report = inv[min(len(calls)-1, len(inv)-1)]
        return {"exit_code": 0, "stdout": json.dumps(report), "stderr":"", "sandbox": {"docker_invoked": False}}
    monkeypatch.setattr(inference,"run_isolated",fake_docker)
    result=inference.analyse(tmp_path,validate_report=lambda r:_check_evidence(r,tmp_path))
    assert result["attempts"]==2
    assert len(result["iterations"])==1
    assert result["report"]["findings"][0]["invoice_ref"]=="INV-1001"
    assert len(calls)==2


def test_agent_fails_closed_after_three_retries(monkeypatch, tmp_path):
    generate(tmp_path)
    monkeypatch.setenv("VULTR_INFERENCE_API_KEY", "TEST_ONLY")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_: object()))
    monkeypatch.setattr(inference, "ask_model", lambda *_: ("print('test')", "deepseek-v4.1-flash-1017"))
    attempts=[]
    def fake_docker(*_):
        attempts.append(1)
        return {"exit_code": 0, "stdout": '{"findings":[],"analysed_invoices":false}', "stderr":"", "sandbox": {}}
    monkeypatch.setattr(inference,"run_isolated",fake_docker)
    with pytest.raises(sandbox.SandboxError,match="after three corrections"):
        inference.analyse(tmp_path)
    assert len(attempts)==4


def test_docker_absent_does_not_execute_python_on_host(monkeypatch, tmp_path):
    generate(tmp_path)
    commands=[]
    def no_docker(cmd,*_,**kwargs):
        commands.append(cmd)
        raise FileNotFoundError("docker not installed")
    monkeypatch.setattr(sandbox.subprocess,"run",no_docker)
    with pytest.raises(sandbox.SandboxError,match="NOT run"):
        sandbox.run_isolated('print("safe")', tmp_path)
    assert commands and all(command[0]=="docker" for command in commands)


def test_health_never_claims_deployed(monkeypatch):
    monkeypatch.setenv("VULTR_INFERENCE_API_KEY","TEST_ONLY")
    assert TestClient(app).get("/health").json()["vultr_deployment"] == "not-verified"
