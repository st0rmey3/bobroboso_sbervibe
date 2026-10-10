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

Локальная модель: см. [docs/llm.md](docs/llm.md). Сброс всех данных: `make reset`.

## Документация
- [Архитектура и схема](docs/architecture.md)
- [Журнал решений](docs/decisions.md)
- [Работа с моделью и локальный запуск](docs/llm.md)
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
