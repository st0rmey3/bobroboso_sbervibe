---
id: T-006
title: Local provider ready: pick model, benchmark, instructions
owner: gemini
status: todo
prio: P0
depends: T-003
---
## Goal
Section 5.3 + С19–С20 (15 pts). Ollama vision model choice justified by numbers on the open set; instructions + files to run it.

## Acceptance
- [ ] docs/llm.md: how to run locally (native macOS + docker profile), hardware needs, model choice table
- [ ] eval numbers for local vs cloud
- [ ] switching provider = only env change

## Notes


## Thread
- [claude] On RTX 5060: native Ollama, `ollama pull qwen2.5vl:7b`; .env: LLM_PROVIDER=ollama, OCR_PROVIDER=none, OLLAMA_URL=http://host.docker.internal:11434. Measure time/quality, write docs/local-model.md step by step.

## Result
