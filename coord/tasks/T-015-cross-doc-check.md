---
id: T-015
title: Bonus: cross-document consistency (name/birth date across documents, Latin vs Cyrillic)
owner: claude
status: done
prio: P0
model: opus
depends: 
---
## Goal
Application-level warnings: full_name / birth_date differ between documents of one person (passport vs patent), or differ from the name the applicant typed. Must compare Cyrillic and Latin spellings (transliteration, ignore case/ё/word order of given names). Shown to operator as warnings; never auto-reject.

## Acceptance
- [ ] applications.py: cross_checks(app) → list of warnings, in operator card schema
- [ ] unit tests: same person Cyrillic/Latin → no warning; different surname → warning
- [ ] no false alarm on the open set

## Notes
Keep the transliteration table small and explainable (GOST-like), one function.

## Thread

## Result
backend/app/crosscheck.py: names → Latin transliteration + spelling variants, one-to-one word match (similarity 0.75),
patronymic may be missing. Checks typed name vs each document, documents vs each other, birth dates. Wired into
ApplicationOperator.cross_checks and application status (mismatch → needs_review); operator edit re-computes status.
Live: 0 false alarms on open-set applications; typed «НеМаксим Чернецов» vs «КИСЕЛЕВ МАКСИМ» → warning. UI: T-022 (codex).
