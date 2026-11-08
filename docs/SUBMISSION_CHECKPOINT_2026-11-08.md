# ExceptionForge — Submission Checkpoint (8 November 2026)

## What has been demonstrated

- **Challenge:** Vultr: Agent Rush Hackathon 2026 — Challenge 1, Blast Radius Zero, Pattern A (sandboxed code).
- **Public demo:** http://45.77.230.86/ — deterministic local workflow using synthetic purchase orders, goods receipts and invoices.
- **Public demo result:** 32 invoices analysed; 15 findings; row-level evidence visible in Evidence Inspector.
- **Vultr Serverless Inference:** real request to `deepseek-v4.1-flash-1017` succeeded.
- **Full live chain (reported by operator):** AI-generated Python executed inside Docker; source-reference evidence validation passed; 32 invoices analysed; 18 findings; 1 model attempt; 9.85 seconds.
- **Docker containment probe:** attempted network access failed with `[Errno 101] Network unreachable`; this proves the specific probe only, not complete sandbox security.
- **Automated test suite after server-side fix:** 55 passed, 1 warning.
- **Public protection:** live analysis and containment endpoints returned HTTP 403 through Nginx. The public demo is deterministic and not an AI run.

## Critical distinctions

1. **15 findings (local)** and **18 findings (AI live)** are different outputs from different execution modes. Their financial correctness has **not** been comprehensively checked against ground truth.
2. The live successful run required a **server-side patch in `app/inference.py`** for reasoning-off generation, disallowing dunder code and diagnosing empty stdout. **The public repository branch is not verified to contain this patch.** Do not claim it does until synchronised and tested.
3. The successful live run needed no autocorrection. A full successful self-correction sequence is **not** demonstrated.
4. The AI/containment result slides in the edited video summarise actual recorded terminal outputs from prior runs; they are **not** screen recordings of those runs.
5. The deployed public app uses HTTP for synthetic data only and does not expose live AI calls to jurors.

## Video artefacts

A private, complete handoff bundle, including the 72.92-second Full-HD subtitled MP4, original Playwright browser capture, proof graphics, SRT captions and detailed handoff instructions, was archived separately to Google Drive on 8 November 2026. The edited MP4 has **no final narration**. Do not claim audio is complete.

## Remaining submission gates

- Verify current lablab.ai submission requirements, deadline, licence and judging accessibility.
- Confirm code parity between Vultr host and GitHub. Do not modify a stable branch without separate approval.
- Verify required cover image, deck, video destination and submission form.
- Submit and archive the platform's actual success confirmation.

This file is an **archival status record**, not evidence of completed submission or a production security certification.
