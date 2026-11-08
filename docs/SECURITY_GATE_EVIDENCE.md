# ExceptionForge Stage 2.2 — security-gate evidence

**08/11/2026 — local-only; no server/cloud deployment.**

## Fixes

1. Fail-closed feature flag for both billable live AI and privileged Docker probe.
2. Bearer token supplied by server environment, compared using constant-time comparison; no auth in URL, cookies, or hardcoded browser source.
3. Process-wide sliding limits and concurrency limits for live/localhost mode; rejected calls have explicit 429 and Retry-After.
4. Docker CLI, daemon and image-preload preflight *before* any AI call.
5. AI response `max_tokens=4096` per attempt; up to three existing automatic corrections.
6. Client-side password input only shown when live mode selected; still allows local-only demo.

## Test coverage / limitations

- Unit and local HTTP tests include negative auth, disabled feature flag, missing provider key, quota and contention, container readiness, corrected upload-path tests, synthetic local fixture and upload errors.
- Mocked model/probe success paths are **not Vultr/Docker integration tests**.
- Docker real execution, network-containment probe, Vultr VM, Vultr Serverless Inference, external deployment, financial quota enforcement, proxy TLS and external vulnerability testing are **not verified**.
- Per-process in-memory quotas can be bypassed by restarts or multi-worker deployments. A proper public system requires externally shared rate limits, account billing controls and reverse-proxy body limits.

**Do not publish the environment token or actual Vultr API credentials. Do not claim production security.**
