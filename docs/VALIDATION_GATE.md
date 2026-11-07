# ExceptionForge — technical decision gate

**Date:** 04/11/2026 | **Track:** Blast Radius Zero, Pattern A | **Status:** UNVERIFIED

## What must be demonstrably true before GO

| Requirement | Test | Acceptance |
|---|---|---|
| Detection | Gold labels withheld from agent; run model on 15 planted anomalies | >=14/15 detected, with exact invoice identifiers |
| Precision on clean cases | Count any clean invoice flagged, including valid partial delivery and split invoice | 0 false positives |
| Autocorrection | Count model retries after initial generated program | <=3 |
| Time | End-to-end local elapsed timer, from accepted upload to report | <180 seconds |
| Actual inference | Record Vultr request and returned model ID, token usage if available | Live response from requested model, no mock or fallback |
| Real sandbox | Run fixed network probe through same Docker runner | Actual blocked connection; never simulated |
| Failure safety | Test missing key, missing Docker and invalid CSV | No generated code runs on host; errors clearly shown |
| Deployment | On an approved Vultr VM, repeat tests and capture dated logs | End-to-end evidence from actual submission environment |

**Decision by evening 04/11/2026:** if any mandatory criterion fails, simplify the synthetic fixture once, retest against the SAME immutable truth and declare NO-GO if it still fails. A failed security gate cannot be bypassed by simplification.

## Provenance and honest limitations

- The test generator is procedural and the benchmark gold truth is stored separately from the CSV files. These are **synthetic data**, not measurements of customer procurement operations.
- Findings cite source file rows, and the API verifies those rows actually exist. This does not prove the financial interpretation. The gold dataset provides the external test oracle.
- **Model-generated Python** may fail to infer aliases, carton conversion or consolidated invoices. This risk has not been resolved merely by creating code.
- **Vultr billing** and inference credits remain unverified without an authenticated account. Do not activate paid resources without separate express approval.
- **Docker security** is layered but is not a formally proven isolation boundary. For production safety, use hardened hosts, rootless Docker or gVisor and additional independent adversarial verification.

## Evidence package to retain

Keep the real API model ID, end-to-end JSON, independent evaluation JSON, container command, containment result, UTC timestamp, VM instance type, git commit SHA, and screenshots of UI states. Strip keys and all account-specific secrets. Do not substitute screenshots of a simulation for proof of live tests.

## Current local status

- Synthetic generator created; truth file is outside mounted data folder.
- API/UI authored; tests runnable locally.
- Docker execution and Vultr inference: **not verified** in this work environment.
- Vultr VM / hosted URL: **not deployed**.
