---
id: T-019
title: Observability: request id in logs, queue numbers in health
owner: claude
status: todo
prio: P2
model: sonnet
depends: 
---
## Goal
Middleware: X-Request-ID (generate if absent) in every log line of a request; log method/path/status/ms. Worker logs job id + document id + stage timings. /api/health adds queue counts.

## Acceptance
- [ ] one request can be traced in backend logs
- [ ] no personal data in logs (no field values)

## Notes


## Thread

## Result
