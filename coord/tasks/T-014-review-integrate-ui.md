---
id: T-014
title: Review and integrate Codex UI: contract fixes, hard rules, E2E through the UI
owner: claude
status: doing
prio: P0
model: opus
depends: T-004,T-005
---
## Goal
As Codex pushes: review diffs against AGENTS.md §1 (no mock data, server decides, no tokens in URLs), fix backend contract gaps it reports in Threads, run the full scenario through the real UI on the local stand.

## Acceptance
- [ ] every Codex commit reviewed (Thread note or done)
- [ ] applicant + operator scenario passes through UI only (Д3)
- [ ] no hardcoded lists/labels duplicated from backend

## Notes


## Thread
- [claude] Applicant UI E2E vs live backend + real Sber LLM (Playwright, 375 px): country → 4 files incl. a receipt → statuses update without reload → done in 9 s, receipt «Не читается» with reason. Operator UI E2E waits for Keycloak on the stand (T-001/T-012).

## Result
