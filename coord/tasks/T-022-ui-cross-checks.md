---
id: T-022
title: Operator UI: cross-document warnings banner + history labels fallback
owner: codex
status: todo
prio: P0
model: codex
depends: T-015
---
## Goal
Backend (T-015, captain) adds `cross_checks: list[str]` to ApplicationOperator (e.g. «ФИО в заявке «X» не совпадает с документом «Y» (Паспорт РФ)», «Дата рождения различается: …»). Show them at the top of the card as a warning block «Расхождения между документами» (before slots). Also history: field label fallback — use labels from `slot.fields[name].label` when the type is not in `/countries` (P2 from T-021 review). `npm run gen:api` after pull.

## Acceptance
- [ ] card of an application with typed name ≠ document name shows the warning
- [ ] no warning block when list is empty
- [ ] build + tests pass

## Notes


## Thread

## Result
