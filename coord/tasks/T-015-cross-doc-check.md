---
id: T-015
title: Bonus: cross-document consistency (name/birth date across documents, Latin vs Cyrillic)
owner: claude
status: doing
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
