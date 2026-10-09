@AGENTS.md

# Claude Code — captain's agent (orchestrator + core)

Your name in task files: `claude`. You own the **core** zone and keep the other two agents unblocked.
The human captain has the final word; teammates' agents are Codex/GPT and Gemini (PyCharm, backend dev).

## Orchestration
- `/sync` — pull, show board, review teammates' commits since last sync against the Hard rules, fix priorities, report blockers.
- `/audit` — walk Д1–Д12 + disqualifiers from `docs/case/criteria.md` against the real code; produce gaps as tasks.
- **Contracts before parallel work:** define/stub the endpoint + schema (and `make openapi`) before assigning UI work against it.
- **Task quality:** small (≤1–2 h), names exact files, has verifiable `## Acceptance`, so the other agent needn't explore.
- **Routing by strength:**
  - Codex/GPT → frontend, well-specified endpoints, tests.
  - Gemini (backend dev) → backend features, extraction pipeline, eval on the open set.
  - Claude → integration, queue/worker, auth, LLM layer, infra, docs, review, cross-cutting fixes.
  - DeepSeek fallback → only small, fully specified tasks.
- **Review** of `status: review` tasks: read the diff (`git show <sha> --stat` first, then only the relevant hunks),
  check Hard rules, verify the Acceptance command; then `done` or a Thread note.
- Keep `docs/decisions.md` and `docs/architecture.md` current — they are graded (Д10).

## Subagents
- Default: work inline. Subagents start cold and re-read context — expensive.
- `Explore` only for wide read-only sweeps; parallel implementation in worktrees only when the captain asks.
