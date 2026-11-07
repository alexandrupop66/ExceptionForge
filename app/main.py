"""Minimal product API and single-screen interface. No mock inference fallback."""
from __future__ import annotations

import csv
import io
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .inference import analyse
from .sandbox import SandboxError, containment_probe

app = FastAPI(title="ExceptionForge", version="0.1.0", docs_url=None, redoc_url=None)
ROOT = Path(__file__).resolve().parent
FILENAMES = ("purchase_orders.csv", "goods_receipts.csv", "invoices.csv")
MAX_UPLOAD = 300_000
DANGEROUS_NOTE = re.compile(r"(system\s+override|ignore\s+previous|post\s+(all|data)|send\s+.*(records|secrets)|https?://[^\s]+.*exfiltrat)", re.I)


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/health")
def health():
    return {"service": "exceptionforge", "version": "0.1.0", "inference_configured": bool(os.getenv("VULTR_INFERENCE_API_KEY")), "execution_mode": "docker-required", "vultr_deployment": "not-verified"}


def _save_upload(upload: UploadFile, target: Path) -> None:
    raw = upload.file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, detail="Maximum 300 KB per file")
    try:
        value = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(value))
        if not reader.fieldnames or len(reader.fieldnames) > 60 or any(not x or len(x) > 100 for x in reader.fieldnames):
            raise ValueError("Invalid CSV header")
        rows = list(reader)
        if not rows or len(rows) > 3000:
            raise ValueError("CSV must contain 1–3,000 records")
    except (UnicodeError, csv.Error, ValueError) as exc:
        raise HTTPException(422, detail=f"Invalid CSV: {exc}") from exc
    target.write_bytes(raw)
    target.chmod(0o644)


def _source_security_findings(invoice_path: Path) -> list[dict]:
    """Treat invoice notes as data; independently identify a planted adversarial note.

    This scan is NOT a sandbox containment test. The separate live probe proves
    whether Docker blocks networking and is shown independently.
    """
    found = []
    with invoice_path.open(encoding="utf-8-sig", newline="") as handle:
        for number, row in enumerate(csv.DictReader(handle), start=2):
            ref = next((v for k, v in row.items() if k and re.search(r"bill|invoice", k, re.I) and v), None)
            for key, value in row.items():
                if key and re.search(r"note|comment|memo", key, re.I) and value and DANGEROUS_NOTE.search(value):
                    found.append({"invoice_ref": ref or f"row:{number}", "kind": "hostile_instruction_in_invoice_note", "reason": "Untrusted invoice text requests an unauthorised action; no invoice instructions were executed.", "evidence": [f"invoices.csv:{number}"]})
    return found


def _check_evidence(report: dict, data_dir: Path) -> dict:
    """Check cited input rows exist and invoice claims point to actual source rows.

    This validates provenance, not semantic accuracy; independent gold labels
    still determine whether the financial anomaly is real.
    """
    file_rows = {}
    for filename in FILENAMES:
        with (data_dir / filename).open(encoding="utf-8-sig", newline="") as handle:
            file_rows[filename] = list(csv.DictReader(handle))
    validated = []
    for finding in report.get("findings", []):
        if not isinstance(finding, dict) or not isinstance(finding.get("invoice_ref"), str):
            raise SandboxError("Finding lacks an invoice reference")
        if not isinstance(finding.get("reason"), str) or not isinstance(finding.get("evidence"), list) or not finding["evidence"]:
            raise SandboxError("Finding missing reason or evidence")
        linked_invoice = False
        for reference in finding["evidence"]:
            match = re.fullmatch(r"(purchase_orders\.csv|goods_receipts\.csv|invoices\.csv):(\d+)", str(reference))
            if not match:
                raise SandboxError("Invalid evidence format: expected CSV filename:row")
            filename, ntext = match.groups()
            index = int(ntext) - 2  # CSV physical row 1 is header.
            if index < 0 or index >= len(file_rows[filename]):
                raise SandboxError("Evidence points beyond input file")
            if filename == "invoices.csv" and finding["invoice_ref"] in file_rows[filename][index].values():
                linked_invoice = True
        if not linked_invoice:
            raise SandboxError("Ungrounded finding: invoice reference absent from cited source row")
        validated.append(finding)
    for security in _source_security_findings(data_dir / "invoices.csv"):
        if not any(f["invoice_ref"] == security["invoice_ref"] and f.get("kind") == security["kind"] for f in validated):
            validated.append(security)
    report["findings"] = validated
    return report


@app.post("/api/analyse")
def analyse_files(
    purchase_orders: Annotated[UploadFile, File()],
    goods_receipts: Annotated[UploadFile, File()],
    invoices: Annotated[UploadFile, File()],
):
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="exceptionforge-data-") as temp:
        source = Path(temp)
        source.chmod(0o755)  # non-root container requires read-only traversal
        for upload, filename in zip((purchase_orders, goods_receipts, invoices), FILENAMES):
            _save_upload(upload, source / filename)
        try:
            result = analyse(source)
            result["report"] = _check_evidence(result["report"], source)
            result["elapsed_seconds"] = round(time.monotonic() - start, 3)
            result["security_notice"] = "Invoice text was treated as untrusted data. No payment actions are supported."
            return result
        except SandboxError as exc:
            raise HTTPException(503, detail=str(exc)) from exc
        except Exception as exc:
            # Avoid leaking credential, dataset content or vendor API response in HTTP errors.
            raise HTTPException(503, detail="Inference or sandbox execution unavailable; no analysis result was produced") from exc


@app.post("/api/containment-probe")
def probe():
    with tempfile.TemporaryDirectory(prefix="exceptionforge-probe-") as temp:
        path = Path(temp)
        path.chmod(0o755)
        try:
            return containment_probe(path)
        except SandboxError as exc:
            raise HTTPException(503, detail=str(exc)) from exc

