"""Tests for actual deterministic local analysis. NOT tests for Vultr or Docker."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app, _check_evidence
from app.local_analysis import analyse_local
from app.scoring import score
from tools.generate_fixture import generate

ROOT = Path(__file__).resolve().parents[1]


def upload_payload(path: Path) -> dict:
    return {
        name: (name, (path / name).read_bytes(), 'text/csv')
        for name in ('purchase_orders.csv', 'goods_receipts.csv', 'invoices.csv')
    }


def as_fields(payload: dict) -> dict:
    return dict(zip(('purchase_orders','goods_receipts','invoices'),payload.values()))


def test_local_real_http_report_15_15_without_cloud_docker(monkeypatch):
    monkeypatch.delenv('VULTR_INFERENCE_API_KEY', raising=False)
    from app import inference, sandbox
    monkeypatch.setattr(inference, 'analyse', lambda *_a, **_k: (_ for _ in ()).throw(AssertionError('AI invoked')))
    monkeypatch.setattr(sandbox, 'run_isolated', lambda *_a, **_k: (_ for _ in ()).throw(AssertionError('Docker invoked')))
    client = TestClient(app)
    response = client.post('/api/local-analyse', files=as_fields(upload_payload(ROOT / 'demo_data')))
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['engine'] == 'local_rules'
    assert result['model'] is None and result['code'] is None and result['sandbox'] is None
    assert result['attempts'] == 0 and result['report']['analysed_invoices'] == 32
    assert 'No AI/Vultr inference' in result['disclaimer']
    assert 'payment action or external request' in result['disclaimer']
    independent = score(result['report'],ROOT / 'demo_data_truth' / 'ground_truth.json')
    assert independent['found'] == 15, independent
    assert independent['missed'] == []
    assert independent['false_positives'] == []
    assert len(result['report']['findings']) == 15
    assert result['report']['findings'][0]['invoice_ref'] != ''


def test_local_analysis_on_fresh_generated_data_without_truth_in_data_dir(tmp_path):
    data = tmp_path/'source'
    generate(data)
    report = _check_evidence(analyse_local(data),data)
    assert score(report, tmp_path/'source_truth'/'ground_truth.json')['passes_quality_gate']


def test_reconcile_without_static_fixture_ids(tmp_path):
    data = tmp_path/'source'
    generate(data)
    for filename in ('purchase_orders.csv', 'goods_receipts.csv', 'invoices.csv'):
        path = data/filename
        original = path.read_text(encoding='utf-8')
        # The analyzer should discover inconsistencies regardless of arbitrary IDs.
        path.write_text(original.replace('1004','9094'),encoding='utf-8')
    report = _check_evidence(analyse_local(data),data)
    assert any(f['invoice_ref'] == 'INV-9094' and f['kind']=='over_billed_quantity' for f in report['findings'])
    assert not any(f['invoice_ref']=='INV-1004' for f in report['findings'])


def test_mutation_removes_only_corresponding_signal(tmp_path):
    data=tmp_path/'source';generate(data)
    path=data/'invoices.csv'
    with path.open(encoding='utf-8',newline='') as handle:
        reader=csv.DictReader(handle);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        if row['Bill Number']=='INV-1004':
            row['Billed Units']='24';row['Net GBP']='120.00'
        if row['Bill Number']=='INV-1015':
            row['Supplier Note']='Routine invoice'
    with path.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    report=_check_evidence(analyse_local(data),data)
    ids={f['invoice_ref'] for f in report['findings']}
    assert 'INV-1004' not in ids and 'INV-1015' not in ids
    assert 'INV-1005' in ids and 'INV-1008B' in ids


@pytest.mark.parametrize('invalid', ['missing-header','invalid-number','invalid-unit'])
def test_local_returns_clear_422_and_never_fabricates(invalid,tmp_path):
    data=tmp_path/'source';generate(data)
    path=data/'invoices.csv'
    if invalid=='missing-header':
        path.write_text(path.read_text(encoding='utf-8').replace('Bill Number,','Other Column,',1),encoding='utf-8')
    elif invalid=='invalid-number':
        path.write_text(path.read_text(encoding='utf-8').replace(',27,pieces,135.00,',',not-a-number,pieces,135.00,'),encoding='utf-8')
    else:
        path.write_text(path.read_text(encoding='utf-8').replace(',27,pieces,135.00,',',27,gallons,135.00,'),encoding='utf-8')
    response=TestClient(app).post('/api/local-analyse',files=as_fields(upload_payload(data)))
    assert response.status_code==422
    assert 'detail' in response.json() and not response.json().get('report')


def test_samples_exact_files_and_unknown_not_exposed():
    client=TestClient(app)
    for name in ('purchase_orders.csv','goods_receipts.csv','invoices.csv'):
        response=client.get('/api/demo-data/'+name)
        assert response.status_code==200 and response.content==(ROOT/'demo_data'/name).read_bytes()
    assert client.get('/api/demo-data/ground_truth.json').status_code==404
    assert client.get('/api/demo-data/.env').status_code==404


def test_original_vultr_api_still_fails_closed_without_key(monkeypatch, enabled_api):
    monkeypatch.delenv('VULTR_INFERENCE_API_KEY',raising=False)
    response=TestClient(app).post('/api/analyse',files=as_fields(upload_payload(ROOT/'demo_data')),headers=enabled_api)
    assert response.status_code==503
    assert 'key missing' in response.json()['detail']
