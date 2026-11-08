# ExceptionForge (Vultr: Agent Rush 2026) — Stage 2.2 Security Gate

**Status: STAGE 2.2 LOCAL PROTOTYPE (08/11/2026).** Original Stage 1 code authored on 04/11/2026, after the announced competition start. Stage 2 is a controlled packaging, validation, testing and UI iteration. No Vultr VM deployment, no live Serverless Inference call, and no Docker execution has been verified. Never label these as passed until tested on the actual target. Stage 1, Stage 2 and the local demo remain preserved on separate branches and archives.

## Purpose

Investigate procurement exceptions missed by conventional ERP three-way matching when purchase-order, goods-receipt and invoice CSV exports use different schemas, supplier names and units. The agent generates dataset-specific Python via **Vultr Serverless Inference**, runs it in a **restricted Docker container**, and returns evidence-linked exceptions for **human review only**. It cannot approve or initiate payments.

## Why AI is central

The model writes code for *unfamiliar column names, units and cross-file relationships*. The deterministic part validates source references and enforces the runtime boundary. The prototype must demonstrate superiority to a static exact-column baseline; this has **not yet been measured**.

## Local setup (Python 3.11+, Docker Engine required for live sandbox only)

```bash
python -m venv .venv
# On Windows PowerShell: .venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate
pip install -e '.[test]'
python -m tools.generate_fixture --output demo_data
python -m pytest -q
```

Before running live inference, create a separate, restricted **Vultr Serverless Inference API key**. Never paste or commit its value. Configure via local environment variables, e.g. (PowerShell):

```powershell
# LOCAL MODE: no credentials needed. Leave EXCEPTIONFORGE_ENABLE_LIVE unset.
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`, then upload the three files in `demo_data` **which contain only CSV files**.

Live API requests are disabled unless explicitly enabled by the server operator. A missing access token, inference key, Docker daemon or pre-pulled Docker image fails closed. No simulated model call or Docker replay is silently substituted. You can view the local interface and run regression tests without credentials or Docker, but a full investigation cannot be completed in that environment.

**Stage 2 improvements:** explicit setuptools package discovery fixes editable installation; strict CSV upload parsing, physical-line evidence references and invoice-ID validation strengthen provenance; invalid cited reports trigger up to three code repairs; 26 local tests pass. The desktop application keeps uploads, results and verification status in one viewport at 1280×720 and 1366×768 in browser layout checks. Mobile uses normal vertical scrolling. Browser-only report previews are simulated **for layout tests only**, never results of a real model run.

### Independently measure quality on the original fixture

Save the live `/api/analyse` JSON output to `result.json` (the report is inside its `report` property), then run:

```bash
python -m tools.evaluate --response result.json --truth demo_data_truth/ground_truth.json
```

**Gate before submission on 08/11/2026 (Europe/London):** at least 14 of 15 planted anomalies detected; zero findings on known-clean invoices; at most three code corrections; less than 180 seconds elapsed; live containment test blocked. If not met, simplify the data once and retest, then decide NO-GO. Do not adjust the gold labels after seeing agent results.

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

- Public MIT GitHub repository (currently private; publication only after user approval).
- Vultr Cloud Compute deployment and public application URL, verified by external access.
- Live Vultr Serverless Inference interactions, verified by logs and real API responses.
- Actual containment moment in video (not just a written claim).
- README, cover image, slide presentation, video, LabLab submission, final confirmation.

## References

- [Competition brief](https://lablab.ai/ai-hackathons/vultr-hackathon)
- [Vultr inference API](https://api.vultrinference.com/docs)

**Competition differentiation:** Unlike generic sandbox demos or invoice-to-payment approval apps, ExceptionForge focuses on data reconciliation across non-standard procurement exports and on source-grounded, reviewable exceptions. This advantage remains an untested hypothesis until benchmarked.

## Stage 2 local verification (07/11/2026)

- Editable installation: tested with `python -m pip install --no-build-isolation --no-deps -e .` (PASS in the provided Linux environment; full dependency resolution on a clean Windows machine has not been re-tested).
- Unit/regression/failure-path tests: `python -m pytest -q` => 26 passed (local/mocked paths only).
- Live local HTTP negative tests: `POST /api/analyse` => 503 (Vultr key absent); `POST /api/containment-probe` => 503 (Docker CLI absent). In both cases the API correctly refuses to claim success.
- Chromium layout tests: 1280×720, 1366×768 and 1440×900 have no page-level scroll in initial state; 1280×720 and 1366×768 have no page-level scroll in report UI preview; 390×844 has responsive mobile layout with deliberate vertical scrolling. These are **static/mocked UI state** verifications, not live inference results.
- Still untested: Vultr Cloud Compute, Vultr Serverless Inference, actual Docker execution or containment, real 15-anomaly recall, deployed public URL.

## Stage 2.1: Local deterministic demonstration (08/11/2026)

This mode is **not** Vultr AI, not an autonomous agent, and not a proof of Docker isolation. It is an explicit, deterministic baseline to show real input-to-report interaction while Vultr access is pending. It must not be misrepresented as fulfilment of the hackathon's mandatory Vultr integrations.

### Start on the Windows laptop (reuse existing Stage 1 virtual environment)

1. Keep Stage 2 intact. Extract `ExceptionForge_Local_Demo_2026-11-08.zip` into a **new folder**, not over Stage 2.
2. Open PowerShell in the extracted `ExceptionForge` folder.
3. Run (adapt the Stage 1 path only if its virtual environment has moved):

```powershell
& "C:\Users\alexa\Desktop\ExceptionForge_Stage1_download\ExceptionForge\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

4. Open `http://127.0.0.1:8000` (refresh if an older browser tab is cached).
5. Leave **Local analysis** selected, click **Load sample CSVs**, then **Run local analysis**. Results include source CSV row citations and a downloadable JSON report labelled `LOCAL`.

The analysis requires no Vultr key, Docker, network access or payments. It accepts the **specific documented sample schema**, not arbitrary ERP exports. Other schemas return a clear error instead of guessed results. The original **Vultr AI (live)** mode and **Test containment** remain separate; without their real dependencies, they continue to fail closed. The bundled `demo_data_truth` is only for offline benchmark testing, never read by the local analyser.

A local test on the synthetic fixture detected all 15 known anomalous invoice IDs with no known-clean IDs flagged. This is **not** an accuracy measurement on real-world procurement data, and does not measure AI inference quality.

## Stage 2.2 targeted security gate (08/11/2026)

**Authorised scope:** restrict inference/Docker endpoints, preserve working local demo, add tests; no cloud infrastructure, purchases or deployment.

- `POST /api/analyse` (Vultr AI) and `POST /api/containment-probe` (Docker) are **disabled by default**, including when a key exists.
- Live activation requires **both** `EXCEPTIONFORGE_ENABLE_LIVE=true` and a randomly generated `EXCEPTIONFORGE_ACCESS_TOKEN` of at least 32 printable ASCII characters, configured **server-side only**. Each live HTTP request must send `Authorization: Bearer <token>`. The UI accepts a *demo access token* only when Vultr AI mode is selected; it keeps the token in memory, not in local storage, URLs or the source code. Do not mistake this token for the Vultr API key.
- All live operations share a process-wide rolling budget: **4 accepted requests per hour, 10 per 24 hours and 1 active request**. `429` includes `Retry-After`. Failed admitted requests consume quota. The separate local-analysis endpoint has a **60/minute, 500/day, 2 concurrent** limit, and needs no credentials.
- Before making any model call, the live API now checks for Docker CLI, working daemon and an **already downloaded** `python:3.12-alpine` image. It does not automatically pull the image or run generated Python on the host. AI completions are capped to **4096 output tokens per attempt**, with a maximum of four attempts already present.
- These limits are **not a financial cap**. Process restarts and multiple Uvicorn workers reset or multiply limits. Use exactly **one worker** for this demo, plus Vultr provider-side spending controls, a trusted TLS reverse proxy, request/body-size controls, private network access to Docker and observability before public deployment. Do not treat the token as sufficient production security.
- The original local analysis and static sample CSVs remain available without the token, but this service is **not approved for untrusted customer data or public exposure** without further hardening.

**When credits and a separate deployment/spend approval are confirmed**, use a unique server-side token, the actual inference credential, a running Docker daemon and a pre-pulled image. Only then should the operator explicitly set the live flag to true. Local browser access via `127.0.0.1` is safe for a demonstration; public access must use HTTPS and a rate-limited reverse proxy. Do not grant judges a reusable admin token in a public repository or presentation.

The Stage 2.2 tests cover rejection without credentials, invalid tokens, quota/concurrency, daemon/image preflight, mocked authorisation success and regression of the 15 synthetic findings. **They do not verify paid inference, a real container, or network isolation.** See `docs/SECURITY_GATE_EVIDENCE.md`.
