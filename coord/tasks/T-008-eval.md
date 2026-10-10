---
id: T-008
title: Ground-truth labels for the open set (by hand) for accuracy measurement
owner: gemini
status: todo
prio: P1
depends:
---
## Goal
To prove quality honestly (30 pts block) we need expected values for the organizers' files. By hand, no AI needed.
For each file in the test set create `data/open/<same name>.json` (data/ is git-ignored) and copy the file next to it:
`{"doc_type": "passport_ru", "fields": {"series": "8021", "number": "183703", "full_name": "АЛЕКСЕЕВА АНАСТАСИЯ ИГОРЕВНА", "birth_date": "2001-07-09"}}`
Field names and doc_type codes: `backend/app/extraction/doctypes.py`. Dates as YYYY-MM-DD, digits without spaces.
Non-documents: `{"doc_type": "unknown", "fields": {}}`. Then send the folder to the captain (not via git).

## Acceptance
- [ ] every test file has a label; captain runs `python scripts/eval_extraction.py data/open`

## Thread

## Result
