---
description: Orchestration sync — pull, board, review teammates' commits, update tasks
---
1. `git pull --rebase`, then `scripts/board.sh`.
2. `git log --since="${ARGUMENTS:-2 hours ago}" --format='%h %an %s' --no-merges` — for teammates' commits, check `--stat` and
   only suspicious hunks against AGENTS.md §1 Hard rules (secrets, model calls in handlers, unauthenticated operator routes,
   in-memory state, sample-specific values, GPL deps).
3. For every task in `review`: verify its Acceptance; mark `done` or add a Thread note.
4. Re-prioritize: P0 = anything blocking admission (Д1–Д12). Create missing tasks with `scripts/new_task.sh`.
5. Commit `coord:` changes and push. Report in Russian, ≤10 lines: blockers, who does what next, risks.
