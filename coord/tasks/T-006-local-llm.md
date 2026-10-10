---
id: T-006
title: Local model on the RTX 5060: run, measure, write docs/local-model.md
owner: gemini
status: todo
prio: P0
depends: T-001
---
## Goal
Case 5.3 + С19–С20 (15 pts): a working local provider, a step-by-step instruction a stranger can follow, numbers.

1. Install Ollama natively (GPU). `ollama pull qwen2.5vl:7b` (fits 8 GB). If available also try `qwen3-vl:8b`.
2. In `.env`: `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen2.5vl:7b`, `OCR_PROVIDER=none`,
   `OLLAMA_URL=http://host.docker.internal:11434`; `docker compose up -d backend worker`.
3. Upload the same 6 files (passport RF, SNILS, INN, patent front+back, blurry photo) via the applicant UI.
   Write down per file: time to «Готово», which fields are right/wrong. Then the same with `LLM_PROVIDER=openai`.
4. Write `docs/local-model.md` in Russian, step by step: requirements (GPU/VRAM/RAM/disk), install Ollama, pull model,
   `.env` switch, restart, how to check it works, table with your numbers (time, quality) local vs cloud,
   what changes: hardware, speed, quality, cost, privacy (case 5.3 last bullet).
5. Commit it yourself (`docs: local model guide`) — your own commits are required by the case.

## Acceptance
- [ ] switching provider is only an `.env` change + restart, shown live
- [ ] docs/local-model.md reproducible on a clean machine
- [ ] numbers table filled with real measurements

## Notes
Model too slow / out of memory → try `qwen2.5vl:3b`, note it in the doc. If Gemini doesn't work — DeepSeek or by hand.

## Thread

## Result
