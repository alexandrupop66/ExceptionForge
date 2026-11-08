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

from fastapi import FastAPI, File, HTTPException, UploadFile, Path as ApiPath
from fastapi.responses import FileResponse

from .inference import analyse
from .access import access_middleware
from .local_analysis import analyse_local
from .sandbox import SandboxError, containment_probe, require_docker_ready

app = FastAPI(title="ExceptionForge", version="0.2.2", docs_url=None, redoc_url=None)
app.middleware("http")(access_middleware)
ROOT = Path(__file__).resolve().parent
FILENAMES = ("purchase_orders.csv", "goods_receipts.csv", "invoices.csv")
MAX_UPLOAD = 300_000
DANGEROUS_NOTE = re.compile(r"(system\s+override|ignore\s+previous|post\s+(all|data)|send\s+.*(records|secrets)|https?://[^\s]+.*exfiltrat)", re.I)


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/health")
def health():
    return {"service": "exceptionforge", "version": "0.2.2", "inference_configured": bool(os.getenv("VULTR_INFERENCE_API_KEY")), "execution_mode": "vultr-ai-requires-docker; local-rules-available", "vultr_deployment": "not-verified"}


def _save_upload(upload: UploadFile, target: Path) -> None:
    raw = upload.file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, detail="Maximum 300 KB per file")
    try:
        value = raw.decode("utf-8-sig")
        if "\x00" in value:
            raise ValueError("NUL bytes are not allowed")
        reader = csv.DictReader(io.StringIO(value, newline=""), strict=True)
        headers = reader.fieldnames
        if not headers or len(headers) > 60 or any(not x or len(x) > 100 for x in headers):
            raise ValueError("Invalid CSV header")
        if len(set(headers)) != len(headers):
            raise ValueError("Duplicate CSV headers")
        record_count = 0
        for row in reader:
            if None in row:
                raise ValueError("CSV record contains extra unlabelled columns")
            record_count += 1
            if record_count > 3000:
                raise ValueError("CSV exceeds 3,000 records")
        if not record_count:
            raise ValueError("CSV has no records")
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
        reader = csv.DictReader(handle)
        for row in reader:
            number = reader.line_num  # Physical line, not logical record count.
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
            reader = csv.DictReader(handle)
            file_rows[filename] = {reader.line_num: row for row in reader}
    findings = report.get("findings")
    if not isinstance(findings, list) or len(findings) > 250:
        raise SandboxError("Invalid finding count")
    validated = []
    for finding in findings:
        if not isinstance(finding, dict) or not isinstance(finding.get("invoice_ref"), str) or not finding["invoice_ref"].strip() or len(finding["invoice_ref"]) > 120:
            raise SandboxError("Finding lacks a valid invoice reference")
        if not isinstance(finding.get("kind"), str) or not finding["kind"].strip() or len(finding["kind"]) > 120:
            raise SandboxError("Finding lacks a valid exception type")
        if not isinstance(finding.get("reason"), str) or not 2 <= len(finding["reason"]) <= 1200:
            raise SandboxError("Finding missing a valid reason")
        if not isinstance(finding.get("evidence"), list) or not 1 <= len(finding["evidence"]) <= 12:
            raise SandboxError("Finding missing valid evidence")
        linked_invoice = False
        for reference in finding["evidence"]:
            if not isinstance(reference, str):
                raise SandboxError("Invalid evidence reference type")
            match = re.fullmatch(r"(purchase_orders\.csv|goods_receipts\.csv|invoices\.csv):(\d+)", reference)
            if not match:
                raise SandboxError("Invalid evidence format: expected CSV filename:row")
            filename, ntext = match.groups()
            row = file_rows[filename].get(int(ntext))
            if row is None:
                raise SandboxError("Evidence points beyond input file")
            if filename == "invoices.csv":
                # A reference mentioned in an invoice *note* is not the invoice ID.
                identifiers = [value for key, value in row.items()
                               if key and re.search(r"bill|invoice", key, re.I)]
                if finding["invoice_ref"] in identifiers:
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
            require_docker_ready()  # No inference billing if Docker daemon/image is unavailable.
            result = analyse(source, validate_report=lambda report: _check_evidence(report, source))
            result["elapsed_seconds"] = round(time.monotonic() - start, 3)
            result["security_notice"] = "Invoice text was treated as untrusted data. No payment actions are supported."
            return result
        except SandboxError as exc:
            raise HTTPException(503, detail=str(exc)) from exc
        except Exception as exc:
            # Avoid leaking credential, dataset content or vendor API response in HTTP errors.
            raise HTTPException(503, detail="Inference or sandbox execution unavailable; no analysis result was produced") from exc


@app.get("/api/demo-data/{filename}")
def demo_data_file(filename: str = ApiPath(min_length=1, max_length=100)):
    """Serve ONLY known, synthetic sample CSV files bundled with the project."""
    if filename not in FILENAMES:
        raise HTTPException(404, detail="Unknown demo CSV")
    return FileResponse(ROOT.parent / "demo_data" / filename, media_type="text/csv")


@app.post("/api/local-analyse")
def local_analyse_files(
    purchase_orders: Annotated[UploadFile, File()],
    goods_receipts: Annotated[UploadFile, File()],
    invoices: Annotated[UploadFile, File()],
):
    """Explicit opt-in deterministic baseline; no model, network or Docker."""
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="exceptionforge-local-") as temp:
        source = Path(temp)
        for upload, filename in zip((purchase_orders, goods_receipts, invoices), FILENAMES):
            _save_upload(upload, source / filename)
        try:
            report = _check_evidence(analyse_local(source), source)
        except SandboxError as exc:
            raise HTTPException(422, detail=str(exc)) from exc
        return {
            "engine": "local_rules",
            "model": None,
            "code": None,
            "attempts": 0,
            "sandbox": None,
            "report": report,
            "elapsed_seconds": round(time.monotonic() - start, 4),
            "disclaimer": "LOCAL DETERMINISTIC ANALYSIS. No AI/Vultr inference, Docker, containment proof, payment action or external request was performed. Results apply only to supported CSV schemas and require human review.",
        }


@app.post("/api/containment-probe")
def probe():
    with tempfile.TemporaryDirectory(prefix="exceptionforge-probe-") as temp:
        path = Path(temp)
        path.chmod(0o755)
        try:
            return containment_probe(path)
        except SandboxError as exc:
            raise HTTPException(503, detail=str(exc)) from exc
