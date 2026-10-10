---
id: T-003
title: Tune prompts on the open set using T-008 labels (eval numbers)
owner: claude
status: todo
prio: P1
model: sonnet
depends: T-002
---
## Goal
Fill backend/app/extraction/doctypes.py with the 8 types from docs/case/spec.md; tune prompts.py; add per-type validators (dates, number formats, expiry).

## Acceptance
- [ ] each of 8 types: classification + extraction run on the open set (Д11)
- [ ] `python scripts/eval_extraction.py data/open` reports type_acc and field_acc
- [ ] no sample-specific values in code (AGENTS.md §1)
- [ ] unit tests for new validators

## Notes
Suggested owner: gemini (backend). Zone: extraction.

## Thread
- [claude] Registry/rules for 8 types done by claude. Left: tune prompts.py on the open set, report eval numbers here. No sample-specific values!

## Result
