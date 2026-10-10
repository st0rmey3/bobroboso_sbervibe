---
id: T-011
title: Verify OCR stage with Sber olmOCR server
owner: claude
status: todo
prio: P0
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

## Result
