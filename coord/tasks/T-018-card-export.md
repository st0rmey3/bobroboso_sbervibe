---
id: T-018
title: Bonus: applicant card export for HR (CSV/JSON file)
owner: claude
status: todo
prio: P1
model: sonnet
depends: 
---
## Goal
GET /api/operator/applications/{id}/export.csv — one row per field: document, field label, value, source (model/operator), confidence, issues. Content-Disposition attachment with the applicant's name. Audit event `card_exported` (who exported personal data).

## Acceptance
- [ ] behind require_operator
- [ ] audit event written
- [ ] opens in Excel
- [ ] `make openapi` + note for Codex

## Notes


## Thread

## Result
Добавлен `GET /api/operator/applications/{id}/export.csv`, пишет аудит `card_exported`. Проверка: `pytest tests/test_exports.py`. Codex: кнопка «Экспорт карточки» в T-005.
