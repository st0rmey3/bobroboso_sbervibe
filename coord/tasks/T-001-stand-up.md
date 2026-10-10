---
id: T-001
title: Stand up the whole stack on the demo PC (Docker)
owner: gemini
status: todo
prio: P0
depends:
---
## Goal
The RTX 5060 PC is the demo stand (Д1). Bring it up exactly by README, by hand — so we know the README works.

1. `git clone https://github.com/st0rmey3/bobroboso_sbervibe.git && cd bobroboso_sbervibe`
2. `cp .env.example .env`, put the values the captain sends privately (LLM key etc.). Never commit `.env`.
3. `docker compose up -d --build`  (or `make up`), then `docker compose ps` — all services Up.
4. Open http://localhost:3000 (applicant) and http://localhost:3000/operator → Keycloak login page →
   `operator` / OPERATOR_PASSWORD from `.env` → back in the operator UI. If the password doesn't work, check the realm
   import placeholder `${OPERATOR_PASSWORD}` in `keycloak/realm-docs.json` (write the result in Thread — important).
5. Upload 2–3 files from the organizers' test set (captain shares the folder) and watch statuses change.
6. Restart test: while a document is processing run `docker compose restart worker` — it must still finish.

## Acceptance
- [ ] every README step worked as written (or the Thread says which one didn't and the exact error)
- [ ] a document went to «Готово»/«Требует проверки» through the real model
- [ ] restart of worker/backend loses nothing

## Notes
Report problems as one line each in Thread: command → error (last 10 lines of `docker compose logs <service>`).

## Thread

## Result
