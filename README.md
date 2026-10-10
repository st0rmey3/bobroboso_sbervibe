# Приём и разбор документов соискателей

Хакатон «СберБизнесВайб», кейс 2 «Документы». Команда **bobroboros**.

Соискатель загружает комплект документов → сервер мгновенно принимает и проверяет файлы → фоновый воркер разбирает
их моделью (тип документа + поля + уверенность) → оператор после входа сверяет результат с оригиналом, правит и
видит очередь.

## Быстрый старт
Нужны Docker (Docker Desktop / OrbStack) и, для локальной модели, Ollama.

```bash
cp .env.example .env          # заполнить пароли (и ключи облачной модели, если нужна)
make up                       # db, keycloak, backend, worker, frontend
```

| Что | Адрес |
|---|---|
| Кабинет соискателя | http://localhost:3000 |
| Рабочее место оператора | http://localhost:3000/operator (логин `operator`, пароль — `OPERATOR_PASSWORD` из `.env`) |
| API (Swagger) | http://localhost:8000/docs |
| Keycloak (админка) | http://localhost:8080 |

## Учётные данные
| Где | Логин | Пароль |
|---|---|---|
| Рабочее место оператора | `operator` | значение `OPERATOR_PASSWORD` из `.env` |
| Keycloak (админка) | значение `KC_BOOTSTRAP_ADMIN_USERNAME` | значение `KC_BOOTSTRAP_ADMIN_PASSWORD` |
| Кабинет соискателя | не нужны (публичная страница) | — |

## Что должно получиться
1. `make ps` — все пять сервисов (`db`, `keycloak`, `backend`, `worker`, `frontend`) в состоянии running/healthy;
   `curl localhost:8000/api/health` → `{"status":"ok",...,"queue":{...}}`.
2. На http://localhost:3000 выбрать страну, загрузить документы — ответ приходит сразу, статусы обновляются по ходу разбора.
3. На http://localhost:3000/operator после входа видна заявка: поля документов, оригинал рядом, правка и перезапуск разбора.
4. Без входа `curl localhost:8000/api/operator/stats` → `401`.

Если в `.env` не задана модель, разбор идёт через `LLM_PROVIDER=ollama` — нужен запущенный Ollama
(см. [docs/llm.md](docs/llm.md)); без неё документы честно получают статус `failed` с понятной причиной.
Сброс всех данных: `make reset`.

## Документация
- [Архитектура и схема](docs/architecture.md)
- [Журнал решений](docs/decisions.md)
- [Работа с моделью и локальный запуск](docs/llm.md)
- [Ограничения и планы](docs/limitations.md)
- [Отчёт об использовании ИИ-ассистентов](docs/ai-report.md)
- [Вопросы кейсодержателю](docs/case/questions.md)
- [Критерии оценки](docs/case/criteria.md) · [ТЗ кейса](docs/case/spec.md)
- [Контракт API (OpenAPI)](docs/api/openapi.json)

## Структура
```
backend/    FastAPI API + воркер разбора (Python 3.12)
frontend/   React SPA: кабинет соискателя и рабочее место оператора
keycloak/   импорт realm для входа оператора (OIDC)
docs/       документация для защиты
coord/      задачи команды (см. AGENTS.md)
```

## Как работает команда
Разработка ведётся с ИИ-агентами (Claude Code, Codex, Gemini). Общие правила для агентов — [AGENTS.md](AGENTS.md),
задачи — `coord/tasks/`, доска — `scripts/board.sh`.
