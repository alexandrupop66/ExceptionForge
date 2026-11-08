# ExceptionForge | Evidence Before Action

**Vultr: Agent Rush Hackathon 2026 · Challenge 1: Blast Radius Zero · Pattern A (Sandboxed Code)**

**Status (08/11/2026):** A working public deterministic demo and a separately verified private Vultr Serverless Inference → generated Python → restricted Docker execution. The code in this branch incorporates the three inference changes recorded during the real server run. Direct byte-for-byte comparison against the live server file has **not** been performed. This prototype is not production-ready.

## Problem and user experience

Procurement teams have to reconcile purchase orders, goods receipts and supplier invoices even when exports use inconsistent field names, supplier aliases and quantity units. ExceptionForge produces reviewable findings with physical CSV row references, rather than approving financial actions.

**Public demonstration:** http://45.77.230.86/

1. Select **Load sample CSVs**.
2. Leave **Local analysis** selected and press **Run local analysis**.
3. Review flagged invoices and source-row references in the evidence inspector; optionally export JSON.

This public flow is explicitly **deterministic local rules**, not Vultr AI or Docker. An external browser check on 08/11/2026 confirmed **32 synthetic invoice records, 15 exception findings**, CSV row citations and the Export JSON control. These are fixture results, not real-world financial accuracy metrics.

## Verified Vultr integration (separate private execution)

| Component | Recorded evidence on 08/11/2026 | Important limitation |
|---|---|---|
| Vultr Cloud Compute | London VM, Ubuntu 24.04; FastAPI behind Nginx | Public UI is HTTP-only; synthetic data only |
| Vultr Serverless Inference | Actual response from `deepseek-v4.1-flash-1017` | Not called by the public local demo |
| AI-generated Python → Docker → source validation | **32 invoices, 18 findings, 9.85 seconds, one attempt, zero corrections** | 18 AI findings not fully evaluated against ground-truth labels; correction loop not demonstrated in this successful run |
| Docker network containment | Real probe returned `[Errno 101] Network unreachable`, `network_probe: BLOCKED`, exit 0 | One network-denial test, not a complete sandbox security audit |
| Server regression suite after patch | **55 passed, one warning** | Historical run recorded on server; not a fresh CI run of this GitHub commit |

The live analysis, generated code and containment checks were executed on the Vultr server; the public Nginx configuration intentionally blocks privileged `POST /api/analyse` from anonymous visitors (HTTP 403). This protects paid inference and Docker execution. The public site must not be used with sensitive financial data.

**Video provenance:** The published demo capture shows the working public deterministic interface. Slides/cards containing the Vultr AI and Docker test outcomes are **textual evidence from earlier real executions**, not recordings of those live executions. The 15 local findings and 18 AI findings must not be conflated.

## Technical architecture

- **FastAPI + Nginx** serve the web interface and three CSV input streams: purchase orders, goods receipts and invoices.
- **Local analysis:** fixed rules on a known synthetic schema, no model API, network or Docker required.
- **Vultr AI mode:** server-side Vultr Serverless Inference generates dataset-specific Python using schema headers and limited sanitised sample rows, not full financial datasets or ground-truth labels.
- **Sandbox boundary:** generated Python runs in `python:3.12-alpine` under Docker with `--network none`, read-only root filesystem, non-root UID, dropped capabilities, `no-new-privileges`, read-only data mounts and resource limits. An AST allowlist filters code before launch but is not independently a security boundary.
- **Verifier:** checks report structure and physical source-row references. It does not establish that every financial interpretation is correct. Findings are human-review suggestions, never payment authorisations.
- **Access controls:** live operations fail closed without server-side credentials and explicit activation; the application also imposes process-local request and concurrency limits. Those limits are not provider spending limits or a production security guarantee.

### Inference compatibility patch

On the server, a targeted patch enabled DeepSeek compatibility by using `extra_body={"reasoning": {"effort": "none"}}`, extending the inference timeout to 45 seconds, strengthening the generated-code prompt against double-underscore identifiers and reporting empty stdout as an execution error. These changes were reproduced in this GitHub branch from the recorded patch description; an exact server-file hash comparison remains outstanding. The original server-side backup and older Git history were not changed.

## Reproduce the local deterministic flow

Prerequisites: Python 3.11+. Docker is needed only for the restricted live AI runner.

```bash
python -m venv .venv
# On Windows PowerShell: .venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate
pip install -e '.[test]'
python -m tools.generate_fixture --output demo_data
python -m pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000, load the sample CSVs and choose Local analysis. No API credential is necessary for that flow. To evaluate a saved private live response against synthetic labels:

```bash
python -m tools.evaluate --response result.json --truth demo_data_truth/ground_truth.json
```

The completed live 18-finding run did **not** preserve a full scored result, so its ground-truth performance remains unknown. The static/local baseline is not a measurement of LLM inference accuracy.

## Security and evaluation limits

- Data in `demo_data/` are synthetic. Do not upload real invoices or credentials to the HTTP demonstration.
- Never commit model API keys or the `EXCEPTIONFORGE_ACCESS_TOKEN`; `.env` and `.env.*` are gitignored except `.env.example`.
- Public AI/Docker endpoints remain intentionally closed; no bypass token is published.
- Docker containment is a single tested network block, not a comprehensive isolation certification.
- The AI does not authorise or initiate a payment. Incorrect suggestions remain possible and require human review.
- The README describes recorded server results, not continuous availability or independently verified business outcomes.

## Project links and licence

- [Public deterministic demo](http://45.77.230.86/)
- [Submitted source branch](https://github.com/alexandrupop66/ExceptionForge/tree/stage2/security-gate-2026-11-08)
- [Competition brief](https://lablab.ai/ai-hackathons/vultr-hackathon)
- [Vultr inference API documentation](https://api.vultrinference.com/docs)
- [MIT licence](LICENSE)

**Hackathon submission status:** The repository and supporting assets are prepared separately from final lablab.ai platform confirmation. A source commit is not proof of successful competition submission.
