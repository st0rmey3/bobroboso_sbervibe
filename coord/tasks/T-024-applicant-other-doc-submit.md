---
id: T-024
title: Applicant: «Другой документ — определим сами» upload + explicit «Отправить комплект» with confirmation
owner: codex
status: review
prio: P0
model: codex
depends:
---
## Goal
Gap: open-set kinds (ВУ РФ/Киргизии, паспорт Беларуси/Индии) belong to no country set, so the applicant UI has nowhere to upload them (Д11 through the UI!). Backend already accepts uploads WITHOUT `declared_type` (model decides by content) and shows them in their own slot or «Нераспознанные файлы».
1. Under the country slots add a block «Другой документ» with a multi-file input that uploads without `declared_type`; after parsing the file appears in the slot of the detected kind (slots come from the server).
2. Case 4 item 1 says «отправка, подтверждение приёма»: add an explicit «Отправить комплект» step — after files are chosen, one button uploads all pending files; then a confirmation panel: «Комплект принят. Номер заявки: <first 8 chars of id>. Принято файлов: N. Разбор идёт в фоне — можно закрыть страницу и вернуться по ссылке». Per-file server errors stay as now.

## Acceptance
- [x] passport_by uploaded via «Другой документ» ends up in «Паспорт гражданина Беларуси» slot
- [x] explicit submit + confirmation with application number
- [x] build + tests pass, 375 px OK

## Notes

## Thread
- [claude] Backend now accepts WEBP (Android photos) and fixes EXIF rotation of phone photos: add `.webp` to `accept` and to the hint «PDF, JPG, PNG или WEBP» in ApplicantPage.
- [claude] Also: history action `file_viewed` → label «Открыт оригинал» (data.filename) in ApplicationCard `actions` map.
- [codex] Claimed per user request. Add pending-file selection across slots, explicit batch submission with per-file results, and an untyped upload block driven by server-detected slots; preserve closed-application and retry behavior. T-023 remains out of scope.

## Result
- Added untyped multi-file selection plus one explicit batch submit, truthful full/partial acceptance receipts with application number, per-file errors, removal, and retry of refused files only.
- New document slots come from the API; file_viewed is labelled «Открыт оригинал» with its filename in operator history.
- Verified API generation, production build and all 22 browser tests, including 375px layout, detected passport_by slot, closed-application race and no duplicate submission; screenshots inspected.
- Browser responses/tokens are synthetic test fixtures only; no live model/Keycloak verification was performed and no production stubs were added.
- Updated frontend/README.md and coord/defense.md for the new submit flow. T-023 remains untouched.
