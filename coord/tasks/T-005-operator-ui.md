---
id: T-005
title: Operator workplace: list+filters, card with original next to fields, edit, reprocess, in-progress view
owner: codex
status: todo
prio: P0
depends:
---
## Goal
`/operator/*` (frontend/src/pages/operator/). Desktop. Case 3.3, scoring С13–С18 (16 pts) — the biggest UI block:
"how much operator work it really saves". Login is OIDC + Keycloak (mandatory): `RequireOperator` already redirects to the Keycloak login page and back
(`/operator/callback`); `operatorApi(path)` adds the Bearer token. Images can't carry the token in `<img src>`, so use
`await operatorFileUrl(docId)` (fetch → blob URL) for originals. Field labels: build a map from
`GET /api/public/countries` → `doc_types[].fields[] {name,label,required}`.

Screens:
1. **Applications** `/operator`: `GET /api/operator/applications?status=&country=&q=` → table: ФИО, страна, статус,
   документы `documents_done/documents_total`, «требуют внимания» `documents_attention`, пришла `created_at`.
   Filters: status, country, search by name. Click → card. Header: nav (Заявки · В работе), logout.
2. **Card** `/operator/applications/:id`: `GET /api/operator/applications/{id}` → `full_name, phone, country, status,
   missing[], slots[], documents[], history[]`.
   - Banner with `missing` doc types.
   - Per slot (document type): LEFT the original(s) — `<img src={await operatorFileUrl(doc.id)}>` (pdf → `<iframe>`),
     zoom on click; RIGHT the merged fields `slot.fields[name] = {value, confidence, issues[], edited_by, document_id}`.
   - Field row: label, editable value, issues in red, confidence < 0.6 highlighted (bonus "what to re-check first"),
     badge «правка оператора» when `edited_by`. Save → `PATCH /api/operator/documents/{document_id}/fields
     {fields: {name: value}}` (if `document_id` is null use the slot's first document).
   - Per file: status label + `status_reason`, button «Разобрать заново» → `POST /api/operator/documents/{id}/reprocess`.
     Collapsible «Что прочитала модель» → `ocr_text` if present.
   - History (`history[]`: actor, action, created_at, data) — bonus "who changed what".
   - Poll the card every 3 s while something is processing.
3. **In progress** `/operator/processing`: `GET /api/operator/processing` (every 2 s) → filename, ФИО, status, attempts,
   last_error, waiting since; numbers from `GET /api/operator/stats` (queued, running, done, failed, avg_processing_ms).
No mock data anywhere — only server data (disqualification otherwise).

## Acceptance
- [ ] without login any /operator page redirects to Keycloak; logout (`userManager.signoutRedirect()`) works
- [ ] filters work on real data
- [ ] original and recognized fields side by side; edit persists and is marked as operator's edit
- [ ] reprocess moves the file back to the queue and the card updates by itself
- [ ] in-progress screen reflects reality while documents are being parsed
- [ ] `npm run build` passes

## Notes
Same dev setup as T-004, plus `docker compose up -d keycloak` (login `operator` / OPERATOR_PASSWORD from `.env`). Statuses' Russian labels — only in `src/statusLabels.ts`.

## Thread

## Result
