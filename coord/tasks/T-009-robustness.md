---
id: T-009
title: Robustness: concurrency, restart mid-job, model failure, observability
owner: claude
status: done
prio: P1
depends: T-001
---
## Goal
Scenarios С11–С12 (10 pts) + parts of С7–С10 (model failure).

## Acceptance
- [ ] 10 uploads at once are processed in parallel (WORKER_CONCURRENCY)
- [ ] `docker compose restart worker` mid-job → job finishes after lease expiry
- [ ] model down → retries then honest `failed`; reprocess works
- [ ] logs show job lifecycle; /api/operator/stats correct

## Notes


## Thread

## Result
Real Postgres + real LLM, 23 open-set files: uploads ≤80 ms, 8 parallel, kill -9 mid-run → nothing lost, all done in 35 s.
Lease keep-alive thread (15 s) + lease 60 s + release own jobs on start. Model outage → honest retry/failed → reprocess OK.
Also: content duplicates (same series+number) flagged per slot; operator edits re-validated on the server.
Defend: jobs/queue.py (claim SKIP LOCKED, extend_lease, release_own), jobs/worker.py (_keepalive, retry_or_fail).
