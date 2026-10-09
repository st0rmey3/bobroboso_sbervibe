---
description: Admission audit — check Д1–Д12 and disqualifiers against the real code
---
Read `docs/case/criteria.md`. For each admission item Д1–Д12 and each disqualifier, find the concrete evidence in code/docs
(file:line or command) or mark it as a GAP. Do not trust task statuses — check code. Where possible verify live
(`make up`, curl without token on operator routes must give 401, restart worker mid-job and see it finish).
Output a table `item | status (ok/gap/risk) | evidence`, then create a P0 task for every gap via `scripts/new_task.sh`.
