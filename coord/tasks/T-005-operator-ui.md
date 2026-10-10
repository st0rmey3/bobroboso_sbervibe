---
id: T-005
title: Operator workplace: queue, card with original + fields, edit, reprocess
owner: claude
status: todo
prio: P0
depends: 
---
## Goal
frontend/src/pages/operator/*. Scenarios С13–С18 (16 pts): save operator's work — side-by-side original and fields, low-confidence first, inline edit, queue numbers.

## Acceptance
- [ ] queue list with status filter + /stats numbers
- [ ] card: original (via operatorFileUrl) next to fields; fields with issues/low confidence highlighted
- [ ] inline edit → PATCH fields; history visible
- [ ] reprocess button for failed/needs_review
- [ ] logout; without login nothing loads (backend 401)

## Notes
Suggested owner: codex.

## Thread

## Result
