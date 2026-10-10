---
id: T-004
title: Applicant UI: country, doc checklist, multi-file upload, live status, re-upload
owner: codex
status: todo
prio: P0
model: codex
depends:
---
## Goal
Page `/` (frontend/src/pages/applicant/). Works on a PHONE first (case 5.2), also desktop. Case 3.1, scoring С1–С3 (12 pts)
+ bonus "system tells what is missing". Types: `src/api/schema.d.ts` (`npm run gen:api`). Helpers: `src/api/client.ts`
(`publicApi(path, appId, init)` adds the X-Application-Token; `applicantToken.get/set`). Labels: `src/statusLabels.ts`.

Flow:
1. Step 1 form: ФИО (required), телефон (optional), страна — options from `GET /api/public/countries`
   (`[{code,label,doc_types:[{code,label,fields}]}]`); show the doc list of the chosen country right away (С2: set adapts).
   Submit → `POST /api/public/applications {full_name, country, phone}` → `{id, token}` → `applicantToken.set(id, token)`,
   put id into the URL (`/?a=<id>`) so a reload restores the application.
2. Step 2 checklist from `GET /api/public/applications/{id}` → `slots[]`
   (`{doc_type,label,required,state: missing|processing|ok|problem, document_ids, missing_fields}`) + `documents[]`
   (`{id,filename,status,status_reason}`). Per slot: label, state badge, its files (status label + `status_reason`),
   `missing_fields` as "не прочитано: …", button «Добавить файлы» (`<input type=file multiple accept=".pdf,.jpg,.jpeg,.png">`).
3. Upload: each file → `POST /api/public/applications/{id}/documents` multipart `file`, `declared_type=<slot.doc_type>`,
   in parallel. 202 → file appears with «В очереди». Error → show server `detail` text verbatim next to the file
   (duplicates, wrong type, size, limits — all decided by the server).
4. After uploads: clear confirmation «Комплект принят, документы разбираются — страницу можно не обновлять».
5. Polling every 2 s while any slot is `processing` (no manual refresh, requirement 2). Stop when nothing is in progress.
6. `missing[]` (doc type codes) → banner «Не хватает: <labels> — пожалуйста, дошлите». Slots in `problem` show reasons
   and the same «Добавить файл» button (re-upload into the same application, requirement 3).
No technical codes or English errors in the UI. Design simple and clear; mobile layout.

## Acceptance
- [ ] choose country → required docs change (RU 3, UZ 3, EU 2) without hardcoding the list
- [ ] several files per document type; same file twice → server message shown
- [ ] statuses move queued → … → done/needs_review/unreadable without page reload
- [ ] reload page → application restored; re-upload into the same application works
- [ ] usable on a 375 px wide screen
- [ ] `npm run build` passes

## Notes
Backend without Docker: see AGENTS.md §9 "Dev without Docker" (SQLite). Real parsing needs LLM settings in `.env` —
ask the captain for the values in a private message (never commit them). Without them documents stay queued/failed —
fine for UI work.

## Thread

## Result
