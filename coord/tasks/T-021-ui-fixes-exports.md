---
id: T-021
title: UI review fixes + operator exports (expiring list, card CSV) + readable code
owner: codex
status: todo
prio: P0
model: codex
depends:
---
## Goal
Review of T-004/T-005 by captain: good work. Fixes, in this order:
1. ~~git author~~ — done (commits now from 4looki). **Don't force-push `main` again** (AGENTS.md §7): if anyone had
   pushed in between, their work would be lost. For future fixes use new commits.
2. **Field labels for all document types (bug):** field labels come from `/countries`, but 4 types are in no country yet
   (driver_license_ru/kg, passport_by/in) → UI shows «Поле документа». Backend now sends `label` in every merged field:
   ApplicationCard.tsx → `specs.find(...)?.label ?? field.label ?? "Поле документа"` (run `npm run gen:api` first).
3. **Exports (bonus, backend ready):**
   - card: button «Выгрузить карточку (CSV)» → `GET /api/operator/applications/{id}/export.csv`;
   - new tab «Истекают» `/operator/expiring`: `GET /api/operator/expiring?days=30` → table (ФИО → link to card,
     документ, поле, дата, дней осталось; negative = «истёк N дн. назад», red) + button «Скачать CSV»
     → `GET /api/operator/expiring.csv?days=30`.
   Downloads need the Bearer token → fetch with `operatorApi`-style headers, then blob → `<a download>`.
4. **Processing page:** `last_error` is now a Russian reason (raw error stays in logs) — keep the column, rename header
   to «Причина».
5. **Readability for the defense (Д12):** run Prettier (`npx prettier --write src`, printWidth 120) — one JSX element
   per line; judges will ask you to explain any function.

## Acceptance
- [x] commits authored with your real name
- [ ] passport_by card shows «Номер», «ФИО», … not «Поле документа»
- [ ] both CSV downloads work with login, Cyrillic opens in Excel
- [ ] `npm run build` + `npm test` pass

## Thread

## Result
