# ExceptionForge (Vultr: Agent Rush 2026) — Stage 1

**Status: LOCAL PROTOTYPE.** Original code authored on 04/11/2026, after the announced competition start. No Vultr VM deployment, no live Serverless Inference call, and no Docker execution has been verified in the provided environment. Never label these as passed until tested on the actual target.

## Purpose

Investigate procurement exceptions missed by conventional ERP three-way matching when purchase-order, goods-receipt and invoice CSV exports use different schemas, supplier names and units. The agent generates dataset-specific Python via **Vultr Serverless Inference**, runs it in a **restricted Docker container**, and returns evidence-linked exceptions for **human review only**. It cannot approve or initiate payments.

## Why AI is central

The model writes code for *unfamiliar column names, units and cross-file relationships*. The deterministic part validates source references and enforces the runtime boundary. The prototype must demonstrate superiority to a static exact-column baseline; this has **not yet been measured**.

## Local setup (Python 3.11+, Docker Engine required)

```bash
python -m venv .venv
# On Windows PowerShell: .venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate
pip install -e '.[test]'
python -m tools.generate_fixture --output demo_data
pytest -q
```

Before running live inference, create a separate, restricted **Vultr Serverless Inference API key**. Never paste or commit its value. Configure via local environment variables, e.g. (PowerShell):

```powershell
$env:VULTR_INFERENCE_API_KEY = "<YOUR_PRIVATE_KEY>"
$env:VULTR_MODEL = "deepseek-v4.1-flash-1017"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`, then upload the three files in `demo_data` **which contain only CSV files**.

A missing key or missing Docker fails closed. No simulated model call or Docker replay is silently substituted.

### Independently measure quality on the original fixture

Save the live `/api/analyse` JSON output to `result.json` (the report is inside its `report` property), then run:

```bash
python -m tools.evaluate --response result.json --truth demo_data_truth/ground_truth.json
```

**Gate by evening 04/11/2026 (Europe/London):** at least 14 of 15 planted anomalies detected; zero findings on known-clean invoices; at most three code corrections; less than 180 seconds elapsed; live containment test blocked. If not met, simplify the data once and retest, then decide NO-GO. Do not adjust the gold labels after seeing agent results.

## Defence in depth

- The model never receives ground-truth labels, full CSVs or invoice note text. It receives schema headers and two sanitised sample rows. Full CSVs are read **only by code executing in Docker**.
- Docker launch: `--network none`, `--read-only`, all capabilities dropped, no-new-privileges, non-root UID, 256 MiB, 0.5 CPU, 64 PIDs, isolated temporary directory, read-only mounts.
- Python AST allowlist prevents *some* unsafe generated programs before container execution; it is not a security boundary in itself.
- A **fixed live containment probe** tries to connect to the documentation-only address `192.0.2.1` from a real container using the same restricted runner. Kernel failure and exit status decide PASS/FAIL; never fake a PASS.
- A **separate untrusted-note detector** flags the planted malicious invoice. This is an invoice security exception, **not itself proof of containment**.
- Dataset references are checked to exist in source files. This does **not** independently validate all financial reasoning yet. A benchmark with ground truth is required.
- All data in `demo_data` are synthetic. Do not upload real supplier or financial information to an externally hosted demo without separate approval, privacy assessment and access controls.
- **Docker engine access is highly privileged**. This is an experiment, not a production-grade isolation guarantee. Prefer dedicated short-lived Vultr VM, engine hardening and additional isolation (gVisor/rootless) before using untrusted users' data.

## Live test checklist

1. Docker Engine available; fixed image `python:3.12-alpine` pulled (pulling may use internet on the VM). Validate the exact image/digest for repeatability.
2. Inference key configured with billing cap. Confirm actual model ID in API response; model fallback to a different ID is rejected.
3. Start app locally. `/health` should show inference configured but *not* claim Vultr deployed.
4. Run the live containment probe. Capture raw kernel-level error, Docker flags, time and host environment.
5. Run analysis on fixture. Save full JSON privately and evaluate against gold truth without model access to truth file.
6. Test invalid CSV, timeout, missing credentials, no Docker, malicious note, concurrent requests and unauthorised access.
7. Deploy only after explicit approval and account/cost confirmation. Public demo requires TLS, request throttling, resource quotas, monitoring and a defensible access policy.

## Hackathon submission (not yet complete)

- Public MIT GitHub repository (this package has MIT license, but has not been published).
- Vultr Cloud Compute deployment and public application URL, verified by external access.
- Live Vultr Serverless Inference interactions, verified by logs and real API responses.
- Actual containment moment in video (not just a written claim).
- README, cover image, slide presentation, video, LabLab submission, final confirmation.

## References

- [Competition brief](https://lablab.ai/ai-hackathons/vultr-hackathon)
- [Vultr inference API](https://api.vultrinference.com/docs)

**Competition differentiation:** Unlike generic sandbox demos or invoice-to-payment approval apps, ExceptionForge focuses on data reconciliation across non-standard procurement exports and on source-grounded, reviewable exceptions. This advantage remains an untested hypothesis until benchmarked.
