---
id: T-009
title: Robustness: concurrency, restart mid-job, model failure, observability
owner: claude
status: doing
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
