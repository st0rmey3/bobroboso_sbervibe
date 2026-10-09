# Coordination

The repo is the only channel shared by all agents (Claude, Codex, Gemini, DeepSeek). Protocol: AGENTS.md §6.

- `scripts/board.sh` — open tasks (`scripts/board.sh codex`, `scripts/board.sh todo`).
- `scripts/new_task.sh "Title" [owner] [prio]` — new task file.
- Task lifecycle: `todo → doing → review → done` (or `blocked` with a Thread note saying on what).
- Owner names: `claude`, `codex`, `gemini`, `deepseek`, `unassigned`.
