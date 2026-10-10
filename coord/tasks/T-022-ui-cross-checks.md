---
id: T-022
title: Operator UI: cross-document warnings banner + history labels fallback
owner: codex
status: review
prio: P0
model: codex
depends: T-015
---
## Goal
Backend (T-015, captain) adds `cross_checks: list[str]` to ApplicationOperator (e.g. «ФИО в заявке «X» не совпадает с документом «Y» (Паспорт РФ)», «Дата рождения различается: …»). Show them at the top of the card as a warning block «Расхождения между документами» (before slots). Also history: field label fallback — use labels from `slot.fields[name].label` when the type is not in `/countries` (P2 from T-021 review). `npm run gen:api` after pull.

## Acceptance
- [x] card of an application with typed name ≠ document name shows the warning
- [x] no warning block when list is empty
- [x] build + tests pass

## Notes


## Thread
- [codex] Accepted per user request. First priority: regenerate API types, show cross-document warnings, verify history labels, and run build/browser checks.

## Result
- Shows server cross_checks in a named warning section before document slots; hides the section when no warnings remain.
- History already resolves labels from the source slot; the passport_by browser regression confirms labels without a country catalog.
- Verified API generation, production build, and 16/16 browser tests, including warning ordering and removal after correction.
- Browser fixtures are test-only; no demo mode or authentication bypass was added. Live stand acceptance remains separate.
