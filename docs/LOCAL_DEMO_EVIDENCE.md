# Local deterministic demonstration evidence, 08/11/2026

**Scope:** Explicit local rules mode only. No live Vultr, no real Docker, no claimed cloud deployment.

- Command `python -m pytest -q`: **35/35 PASS** on the worktree before packaging.
- Fixture: three synthetic CSV files, 30 purchase orders, 31 goods-receipt rows, 32 invoice records.
- Independent ground-truth comparison: **15/15 anomalous invoice identifiers found, 0 additional invoice identifiers flagged**. Distinct anomaly *types* were not independently scored.
- Adversarial test: changing a planted anomalous invoice to matching values causes its finding to disappear, likewise a malicious note replaced with ordinary note.
- ID mutation: invoice number `INV-1004` changed across files to `INV-9094` and the mismatch followed the new ID; it is not hardcoded to the original ID.
- The FastAPI `/api/local-analyse` endpoint was exercised via TestClient using multipart CSV uploads, with AI/Docker functions patched to fail if called. Output has `engine: local_rules`, `model: null`, `code: null` and `sandbox: null`.
- Negative cases: missing CSV columns, invalid quantities and unsupported units all return HTTP 422 without a report. Existing `/api/analyse` still returns HTTP 503 for missing Vultr key.
- UI Chromium tests with actual HTML/JavaScript and real ASGI request handlers behind a test transport adapter at 1366x768, 1280x720 and 390x844: three sample CSVs loaded, 15 findings shown, navigation and JSON export verified, no JavaScript errors. Browser sandbox prevented Chromium's direct HTTP navigation, so **the browser transport was adapted in the test**; independent HTTP tests cover the actual ASGI endpoint. This is not a public deployed browser test.
- At 1366x768 and 1280x720, Chromium reported no document-level horizontal or vertical scroll; mobile remains vertically scrollable by design.

### Boundaries / interpretation

The rule-based analyser is restricted to the header names and field semantics documented by the synthetic sample. It tolerates basic Ltd/Limited aliases, but does not verify real supplier identity. Findings are *review candidates*, not proof of fraud. The security note detector is separate from, and does not validate, Docker containment. `main` and Stage 2 are preserved; this is a separately archived experimental branch/version.
