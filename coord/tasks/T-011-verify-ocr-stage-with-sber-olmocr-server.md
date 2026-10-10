---
id: T-011
title: Verify OCR stage with Sber olmOCR server
owner: claude
status: blocked
prio: P1
model: sonnet
depends:
---
## Goal
Set OCR_PROVIDER=olmocr + key in .env (never commit), process a real document end-to-end; verify prompt/front matter handling in backend/app/llm/ocr.py.

## Acceptance
- [ ] document goes preprocessing → recognizing → extracting → done/needs_review
- [ ] ocr_text stored and visible to operator
- [ ] OCR down → retries, then honest failed

## Notes

## Thread
- [claude] 12:55: `scripts/check_ocr.py` added. Fixed bug: empty OCR_API_KEY sent an illegal empty Bearer header (OCR could never work without a key). Sber server 195.209.212.175:8000 accepts TCP but doesn't answer HTTP within 30 s → asked the case holder (questions.md A5).

- [claude] Blocked: Sber olmOCR at 195.209.212.175:8000 accepts TCP but doesn't answer HTTP (re-checked 15:40). Local OCR via Ollama added instead.

## Result
