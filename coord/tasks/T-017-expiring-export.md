---
id: T-017
title: Bonus: expiring documents list + CSV export for the operator
owner: claude
status: done
prio: P1
model: sonnet
depends: 
---
## Goal
GET /api/operator/expiring?days=30 → documents whose expiry fields (rules contain not_expired) are past or within N days: applicant, doc type, field, date, days left. GET /api/operator/expiring.csv — same as CSV (UTF-8 with BOM, `;` separator so Excel opens it). Uses merged slot fields (applications.doc_slots).

## Acceptance
- [ ] both endpoints behind require_operator
- [ ] CSV opens in Excel with Cyrillic
- [ ] test for the selection logic
- [ ] `make openapi`; task for Codex to add a button (T-005 Thread)

## Notes


## Thread

- [claude/opus] Reviewed: OK. Added CSV-injection guard in exports._cell. Live-checked: sorted by urgency, 401 without token.

## Result
Добавлены `GET /api/operator/expiring?days=30` и `expiring.csv` (backend/app/exports.py, api/operator.py). Проверка: `pytest tests/test_exports.py`. CSV: UTF-8 BOM, `;`. Codex: добавить кнопку (скачивание с Bearer-токеном, не ссылкой).
