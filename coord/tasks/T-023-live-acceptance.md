---
id: T-023
title: Live acceptance on the PC stand with the stand owner: Д1–Д12 walkthrough, write results
owner: codex
status: doing
prio: P0
model: codex
depends: 
---
## Goal
Judges' checkpoint: Д5, Д6, Д7, Д11 got «−» only because they were not demonstrated. Together with the stand owner, go through `docs/case/criteria.md` on the REAL stand (http://localhost:3000) and record evidence in `coord/acceptance.md` (Russian): for each Д — what you did, what you saw, screenshot name. Must cover: Д5 (fields read from file content — upload a file judges never saw, e.g. a phone photo of any passport), Д7 (statuses go through stages; `docker compose restart worker` mid-processing → finishes), Д11 (all 8 kinds from case_docs parse — use `python scripts/acceptance_run.py` from the captain once pushed), Д6 (switch `.env` to Ollama → same flow works). Report every failure as one line in this Thread, immediately.

## Acceptance
- [ ] coord/acceptance.md with evidence per Д1–Д12
- [ ] every failure reported in Thread

## Notes
Stand owner drives the PC; you drive the checklist and write it down.

## Thread
- [codex] Accepted per user request. Coordinate the real stand walkthrough with its owner; record actual evidence and failures in coord/acceptance.md, without substituting synthetic browser tests.

## Result
