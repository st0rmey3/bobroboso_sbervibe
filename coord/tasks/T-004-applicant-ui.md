---
id: T-004
title: Applicant UI: document set, upload, live status, clear errors
owner: unassigned
status: todo
prio: P0
depends: 
---
## Goal
frontend/src/pages/applicant/*. Scenarios С1–С3 (12 pts): choose/adjust doc set, upload per slot, feedback, understandable errors.

## Acceptance
- [ ] doc set comes from GET /api/public/doc-types (no hardcoded list)
- [ ] upload shows progress and server error text verbatim
- [ ] status polling every 2 s with labels from statusLabels.ts
- [ ] `missing` list shown as 'дошлите …' with upload button (bonus)
- [ ] reload page → application restored (token in localStorage)
- [ ] `npm run gen:api` types used

## Notes
Suggested owner: codex. Backend contract: docs/api/openapi.json.

## Thread

## Result
