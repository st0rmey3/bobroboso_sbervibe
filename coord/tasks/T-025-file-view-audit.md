---
id: T-025
title: Bonus (PII access): audit who opened an original file; show in history
owner: claude
status: done
prio: P1
model: sonnet
depends:
---
## Goal
Bonus «ограничение доступа к файлам с ПДн»: files are already behind Keycloak. Add an audit event `file_viewed` (operator, document_id, filename) in GET /api/operator/documents/{id}/file — at most once per operator per document per 10 minutes (don't spam on re-renders). Frontend history already prints unknown actions; tell Codex the label «Открыт оригинал» in T-024 Thread.

## Acceptance
- [ ] audit row written, deduplicated
- [ ] test
- [ ] history shows it

## Notes

## Thread

## Result
GET /documents/{id}/file writes audit `file_viewed` (operator, filename), deduplicated per operator+document for 10 min. Test + live check: 3 views → 1 event.
