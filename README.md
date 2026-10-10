# Приём и разбор документов соискателей

Хакатон «СберБизнесВайб», кейс 2 «Документы». Команда **bobroboros**.

Соискатель загружает комплект документов → сервер мгновенно принимает и проверяет файлы → фоновый воркер разбирает
их моделью (тип документа + поля + уверенность) → оператор после входа сверяет результат с оригиналом, правит и
видит очередь.

## Быстрый старт
Нужен Docker (Docker Desktop на Windows/macOS или Docker Engine на Linux) и git. Для локальной модели — Ollama.

```bash
git clone https://github.com/st0rmey3/bobroboso_sbervibe.git && cd bobroboso_sbervibe
cp .env.example .env              # Windows PowerShell: copy .env.example .env
docker compose up -d --build      # db, keycloak, backend, worker, frontend (первый раз 5–10 минут)
docker compose ps                 # все пять сервисов — Up
```
`make up` / `make ps` / `make logs s=worker` — то же самое короче (на Linux/macOS, где есть make).

**Что обязательно заполнить в `.env`:**
- пароли `POSTGRES_PASSWORD` (и такой же в `DATABASE_URL`), `KC_BOOTSTRAP_ADMIN_PASSWORD`, `OPERATOR_PASSWORD`;
- модель. Внешняя (по умолчанию для стенда): `LLM_PROVIDER=openai`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`,
  `OPENAI_MODEL`, `OPENAI_DISABLE_THINKING=true`. Локальная: см. [docs/local-model.md](docs/local-model.md).

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
1. `docker compose ps` — все пять сервисов (`db`, `keycloak`, `backend`, `worker`, `frontend`) в состоянии running/healthy;
   `curl localhost:8000/api/health` → `{"status":"ok",...,"queue":{...}}`.
2. На http://localhost:3000 выбрать страну, загрузить документы — ответ приходит сразу, статусы обновляются по ходу разбора.
3. На http://localhost:3000/operator после входа видна заявка: поля документов, оригинал рядом, правка и перезапуск разбора.
4. Без входа `curl localhost:8000/api/operator/stats` → `401`.

Если модель недоступна, документы не «висят» и не получают выдуманных данных: «Сервис распознавания временно
недоступен, повторим автоматически», затем `failed` с причиной и кнопкой повторного разбора у оператора.

**Проверка одной командой** (нужен Python с `pip install httpx`): загружает папку документов как соискатель,
не указывая вид документа, и показывает, что определила модель, стадии и время:
```bash
python backend/scripts/acceptance_run.py case_docs
```

Сброс всех данных: `docker compose down -v` (или `make reset`).

## Если что-то не работает
| Симптом | Причина и что сделать |
|---|---|
| `/operator` → «Не удалось открыть страницу входа» | Keycloak не запустился: `docker compose logs --tail 30 keycloak`. Подождать ~1 мин после старта; затем `docker compose up -d --force-recreate keycloak`. |
| Вход в Keycloak проходит, но список заявок с ошибкой | Открывайте стенд по `http://localhost`, не по IP: адрес выдачи токена должен совпадать с `OIDC_ISSUER`. |
| Поменяли `.env`, ничего не изменилось | `docker compose restart` не перечитывает `.env` и не берёт новый код. Нужно `docker compose up -d --build backend worker`. |
| Скрипт/`curl` к `localhost` получает `503`, а браузер работает | Системный прокси сети. Скрипт приёмки ходит напрямую; для контейнеров в `.env` есть `NO_PROXY=…` — не удаляйте. |
| Документы долго стоят в «Извлечение данных» на локальной модели | Видеокарта не используется или модель не влезает: `ollama ps` должен показывать `GPU`. Настройки для 8 ГБ — в [docs/local-model.md](docs/local-model.md) (`qwen2.5vl:3b`, `WORKER_CONCURRENCY=2`, `IMAGE_MAX_SIDE=1024`). |
| `ollama ps` показывает `100% CPU`, лог Ollama пустой | Запущен контейнер `ollama` из Docker вместо родной Ollama: `docker compose --profile local-llm stop ollama`, перезапустить Ollama. |
| Воркер сразу останавливается | Опечатка в `LLM_PROVIDER`/`OCR_PROVIDER`: `docker compose logs worker` → строка `bad model settings in .env`. |
| Что сейчас включено | `docker compose logs worker` → строка `LLM: … ; OCR: …`; очередь в цифрах — `curl localhost:8000/api/health`. |

## Документация
- [Архитектура и схема](docs/architecture.md)
- [Журнал решений](docs/decisions.md)
- [Работа с моделью](docs/llm.md) · [Переход на локальную модель](docs/local-model.md)
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
