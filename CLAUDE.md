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
  - Stand owner (`gemini`, reads tasks himself, Gemini is limited) → stand, local model, labels.
    His tasks: in Russian, numbered steps, exact commands, `model: human`.
  - Claude → integration, queue/worker, auth, LLM layer, infra, docs, review, cross-cutting fixes.
  - DeepSeek fallback → only small, fully specified tasks.
- **Review** of `status: review` tasks: read the diff (`git show <sha> --stat` first, then only the relevant hunks),
  check Hard rules, verify the Acceptance command; then `done` or a Thread note.
- Keep `docs/decisions.md` and `docs/architecture.md` current — they are graded (Д10).

## Model routing (save Opus limits)
- Task frontmatter `model:` says who should run it: `opus` (design, debugging unknown failures, reviews, cross-cutting),
  `sonnet` (fully specified endpoints, docs, config changes, tests), `human`, `codex`.
- Running a `sonnet` task under Opus is waste: tell the captain to `/model sonnet` first.
- Under Sonnet: follow the task literally; if blocked after 2 attempts — stop, write the blocker in the Thread,
  and suggest switching to Opus.

## Subagents
- Default: work inline. Subagents start cold and re-read context — expensive.
- `Explore` only for wide read-only sweeps; parallel implementation in worktrees only when the captain asks.
