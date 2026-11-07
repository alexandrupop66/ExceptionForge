# Stage 2 verification log — 07/11/2026 (UK)

## Evidence-based status

| Capability | Observation | Result |
|---|---|---|
| Source version | Stage 1 ZIP retained unchanged; Stage 2 built from independent extraction | Verified locally |
| Package installation | `python -m pip install --no-deps --no-build-isolation -e .` | PASS, Python 3.13.5 (local container) |
| Regression suite | `python -m pytest -q` | 26 passed (local/mocked tests) |
| Python compilation | `python -m compileall -q app tools tests` | PASS |
| Browser layout | Chromium viewport checks 1280×720, 1366×768, 1440×900 | No page-level scrollbar, initial UI |
| Browser layout, report UI preview | 1280×720, 1366×768 | No page-level scrollbar, report navigation clickable; data injected only to test layout |
| Mobile layout | 390×844 | No horizontal overflow; normal vertical scroll |
| Negative live HTTP, no key | `POST /api/analyse` with synthetic fixture | HTTP 503; no fabricated result |
| Negative live HTTP, no Docker | `POST /api/containment-probe` | HTTP 503; code not executed |
| Vultr Serverless Inference | No API key or cloud credit confirmed | NOT TESTED |
| Docker containment | No Docker executable available | NOT TESTED |
| 15 planted anomaly benchmark | Needs real Vultr model and sandbox | NOT TESTED |
| Public deployment | No paid resource approval | NOT DEPLOYED |

## Scope and interpretation

The 26 PASS tests comprise API contract, fixture, schema validation, retry, scoring and fail-closed checks. They do not demonstrate real model quality. Browser layout previews are synthetic and **must never be described as an actual AI result**. No benchmark claims are made.

## Outstanding before submission

Obtain authorised cloud access; build and test Docker execution; conduct actual network-containment probe; run model and independently score real output against 15 anomaly labels; verify public URL, costs, credentials and access restrictions; prepare video and presentation. Do not claim any step passed until it is demonstrated.
