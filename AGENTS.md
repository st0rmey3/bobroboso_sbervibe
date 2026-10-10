# AGENTS.md — shared rules for every coding agent

Hackathon «СберБизнесВайб», **Case 2 «Документы»**: an applicant uploads a set of documents → the backend
parses them with an LLM **in the background** → an operator reviews/edits results in a login-protected workplace.

Team (6 h of coding!):
- captain — Claude Code (orchestrator; core + most features, incl. frontend while Codex is away). Name: `claude`.
- backend dev — Aider / PyCharm plugin on free Gemini API (rate-limited → small, fully specified tasks).
  Owns the PC with Docker + Ollama + RTX 5060 8 GB → demo stand host, local model, eval runs. Name: `gemini`.
- Codex/GPT — may join later (frontend). Name: `codex`. DeepSeek harness = fallback for anyone (`deepseek`).
Every human must have commits under their own git name (case 5.4: ≥15 meaningful commits, whole team visible).

Grading: `docs/case/criteria.md` (admission Д1–Д12 + 100 pts + disqualifiers). Full case text: `docs/case/spec.md`
(8 document types and rules: section 4.1). Open questions to the case holder: `docs/case/questions.md`.
Read them before design decisions, not every session.

## 0. Session start (always; cheap)
1. `git pull --rebase`
2. `scripts/board.sh` — open tasks; pick yours (`owner`) or an unowned `todo` with highest prio.
3. Read only your task file + the files it names. Don't scan the whole repo.

## 1. Hard rules — breaking one fails admission or disqualifies the team
- **No fitting to test files.** No filename→answer maps, no values copied from samples. Fields come from file content via the model.
- **Real storage.** Everything that must persist is in Postgres (+ uploaded files in the `files` volume). Never only in process memory, a file in the repo, or only in the queue.
- **Async.** Upload returns immediately (`202`). Parsing happens only in the worker. Never call the model from an HTTP handler.
- **Honest states.** A document becomes `done` only after a real successful model call. Failures → `failed` / `unreadable` / `needs_review` with a human-readable reason (Russian).
- **Restart-safe.** Jobs are leased rows in Postgres; an expired lease is re-claimed. Don't add state that a restart loses.
- **Closed operator side.** Every `/api/operator/*` route and every file download requires a valid OIDC token with role `operator`, checked **on the server**. Frontend guards are cosmetic.
- **Server-side validation** of uploads: size, real type by magic bytes, duplicates (sha256), doc-set rules. Clear Russian error messages.
- **Model isolation.** Model calls only via `backend/app/llm/` (`get_provider()`; provider chosen by `LLM_PROVIDER`). No vendor SDKs/URLs anywhere else.
- **No secrets in git.** Config via env only; every new var goes to `.env.example` with a dummy value.
- **Licenses:** permissive only (MIT/BSD/Apache/ISC/PSF/HPND). No GPL/AGPL (e.g. PyMuPDF is AGPL → we use pypdfium2).
- **Explainable code (Д12).** Each human must explain their part. Prefer plain, boring code over clever abstractions.

## 2. Working style (condensed from Karpathy's guidelines)
1. **Think before coding.** State assumptions. If ambiguous: ask in the task `## Thread`, or take the simplest reading and note it.
2. **Simplicity first.** Minimum code that solves the task. No speculative features, options, or layers.
3. **Surgical changes.** Touch only what the task needs; match local style; don't reformat/refactor others' code.
4. **Goal-driven.** Turn the task into checks (test, curl, UI step), loop until they pass. Never claim "done" unverified.

## 3. Token economy
- **Reason in English.** Reply to humans in **Russian**. Code, identifiers, commits, comments: English.
  UI strings and judge-facing docs (`README.md`, `docs/*.md`): Russian.
- **Terse chat.** No preamble, no restating the task, no recap of unchanged things. Report as:
  `Done: … | Changed: <files> | Verify: <command> | Next/Blocked: …`
  Terseness is for chat only — code, docs and commits stay in normal grammar (others read them).
- **Read narrowly.** `rg`/grep → read the needed line range. Don't re-read files you just edited.
  Never open lockfiles, `node_modules`, build output, `docs/api/openapi.json` (grep it instead).
- **Logs:** `tail -n 50`, `grep -i error`. Never paste whole logs or files into chat.
- **Narrowest check first** (one test / one curl) before full suites or `docker compose build`.
- One recommendation, not a survey of options you won't implement.

## 4. Repo map
```
backend/app/main.py            FastAPI app, routers, startup (create tables)
backend/app/config.py          all settings (env)
backend/app/models.py          SQLAlchemy models + status enums  ← single source of statuses
backend/app/schemas.py         API request/response models        ← HTTP contract
backend/app/auth.py            OIDC (Keycloak) token check, require_operator
backend/app/storage.py         uploaded files on the `files` volume
backend/app/api/public.py      applicant API (no login; per-application token)
backend/app/api/operator.py    operator API (OIDC, role operator)
backend/app/jobs/queue.py      Postgres job queue: enqueue / claim (SKIP LOCKED + lease)
backend/app/jobs/worker.py     worker process: claim → pipeline → retry/fail
backend/app/llm/               model layer: LLM providers (ollama local, gigachat, openai_compat) + ocr.py (olmOCR)
backend/app/extraction/        doctypes.py (countries, 8 doc types, fields, rules), preprocess, prompts, pipeline
backend/scripts/               export_openapi.py, eval_extraction.py
frontend/src/                  React SPA: /  (applicant)   /operator/* (operator, OIDC)
keycloak/realm-docs.json       realm import: client operator-ui, role operator, demo user
coord/tasks/                   task files (the inter-agent channel)
docs/                          criteria, spec, architecture, decisions, llm (judge-facing, Russian)
```

## 5. Contracts — how the parts talk
- **HTTP API:** `backend/app/schemas.py` is the source of truth. After changing an endpoint: `make openapi`
  (commits `docs/api/openapi.json`). Frontend regenerates types with `npm run gen:api`. Never hand-write types that drift.
- **Countries, document types, fields, rules:** only in `backend/app/extraction/doctypes.py`. Frontend gets them from
  `GET /api/public/countries`. Never duplicate the list.
- **Parsing flow:** file → page images → OCR text (`OCR_PROVIDER=olmocr`) → LLM classify → LLM extract → server
  validation. With `OCR_PROVIDER=none` the LLM reads page images itself (local VLM in Ollama).
- **Statuses:** enums in `backend/app/models.py`. UI labels for them live in one frontend file.
- **Breaking a contract** (rename/remove a field, change a status): create a task for the affected owner + note in `docs/decisions.md`.

## 6. Coordination between agents (the repo is the only shared channel)
- **Task = one file** `coord/tasks/T-XXX-slug.md` (frontmatter: id, title, owner, status, prio, depends).
  status: `todo | doing | blocked | review | done`; prio: `P0 | P1 | P2`. Create with `scripts/new_task.sh "Title" [owner] [prio]`.
- **Claim:** set `owner` + `status: doing`, then commit & push right away (`coord: claim T-007`) so nobody duplicates it.
- **Ask / answer:** append one line to the task's `## Thread`: `- [codex] question…` / `- [claude] answer…`.
- **Need work in another zone:** create a task owned by that zone instead of editing their files.
- **Finish:** fill `## Result` (≤5 lines: what changed, how to verify, what the human must know to defend it),
  set `status: review` (or `done` if trivial), push. The captain reviews `review` tasks.
- **Decisions** affecting others or the jury story → append to `docs/decisions.md` (ADR-lite, ≤6 lines).
- Humans relay urgent things verbally; the task file remains the record.

## 7. Git
- Trunk-based: `git pull --rebase`, small commits, push to `main` often (at least every ~40 min of work).
  Branch + PR only for risky or cross-zone changes.
- Commit message: `<zone>: <what>` — e.g. `backend: reject duplicate uploads by sha256`. One logical change per commit.
- Before pushing: your check passes; `git diff --cached` contains no `.env`, keys, real personal data, or `data/`.
- Never force-push `main`. Never rewrite others' commits. Resolve conflicts keeping both sides' intent.

## 8. Ownership zones (people assigned in `coord/tasks/`)
| Zone | Paths | Owner |
|---|---|---|
| core | `docker-compose.yml`, `Makefile`, `backend/app/{main,config,db,models,schemas,auth,storage}.py`, `backend/app/jobs/`, `backend/app/llm/`, `keycloak/`, `coord/`, `docs/` | claude (captain) |
| extraction | `backend/app/extraction/`, `backend/scripts/eval_extraction.py` | claude (rules) · gemini (prompt tuning, eval) |
| backend features | `backend/app/api/`, new modules under `backend/app/` | per task |
| local model & stand | `docs/local-model.md`, `ollama/`, stand runs | gemini |
| frontend | `frontend/` | claude (codex if joins) |

Outside your zone: only through a task assigned to you or an agreement in a Thread.
`models.py` / `schemas.py` are shared hot spots: small additive edits are fine, mention them in your commit message.

## 9. Commands
```
cp .env.example .env              # once
make up                           # docker compose up -d --build (db, keycloak, backend, worker, frontend)
make up-local-llm                 # + ollama container (see docs/llm.md; on macOS prefer native Ollama)
make logs s=worker                # tail one service
make test                         # backend pytest inside container
make openapi                      # regenerate docs/api/openapi.json
make reset                        # drop all volumes (DB schema changed → needed while we use create_all)
scripts/board.sh                  # task board
```
URLs: applicant http://localhost:3000 · operator http://localhost:3000/operator · API docs http://localhost:8000/docs ·
Keycloak http://localhost:8080 (admin creds in `.env`).
Frontend dev without Docker: `cd frontend && npm i && npm run dev` (http://localhost:5173, proxies `/api` → :8000).
