---
id: T-019
title: Observability: request id in logs, queue numbers in health
owner: claude
status: review
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
X-Request-ID (принимается или генерируется) в каждой строке лога запроса `[id]`, итоговая строка метод/путь/статус/мс; воркер пишет `[jobN]`, этапы документа в логе пайплайна; `/api/health` отдаёт `queue`. Значения полей в логи не пишутся. Проверка: `curl -H "X-Request-ID: abc" localhost:8000/api/health -i` и `make logs s=backend`.
