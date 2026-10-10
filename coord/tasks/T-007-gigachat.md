---
id: T-007
title: Verify GigaChat provider with real keys
owner: claude
status: blocked
prio: P2
model: sonnet
depends: 
---
## Goal
backend/app/llm/gigachat.py is written from docs but untested. Verify OAuth, file upload, attachments, JSON output; delete uploaded files after use.

## Acceptance
- [ ] LLM_PROVIDER=gigachat processes a document end-to-end
- [ ] uploaded files deleted after the call
- [ ] errors map to LLMError(retryable) correctly

## Notes
Suggested owner: gemini. Needs GIGACHAT_CREDENTIALS from organizers (never commit).

## Thread
- [claude] Depends on keys (questions.md A1, C14). External = Sber olmOCR + GigaChat (or any OpenAI-compatible).

- [claude] Blocked: no GigaChat keys. External provider = Sber Qwen (OpenAI-compatible) covers 5.3.

## Result
