# Работа с моделью (раздел 5.3)

## Изоляция
Весь код, знающий о конкретных моделях, — в `backend/app/llm/`. Остальная система вызывает только
`get_provider().complete_json(...)` и обрабатывает `LLMError` (с признаком «можно повторить»).

| `LLM_PROVIDER` | Файл | Назначение |
|---|---|---|
| `ollama` | `llm/ollama.py` | **локальная** модель, структурированный вывод по JSON Schema |
| `gigachat` | `llm/gigachat.py` | основная облачная (Сбер), изображения через загрузку файлов |
| `openai` | `llm/openai_compat.py` | любой OpenAI-совместимый API (OpenAI, DeepSeek, OpenRouter, vLLM, LM Studio) |

Переключение — только переменной окружения в `.env` и `docker compose up -d backend worker`.

## Локальный запуск
**macOS (рекомендуется, GPU через Metal):**
```bash
brew install ollama && ollama serve        # или приложение Ollama
ollama pull qwen2.5vl:7b
# .env: LLM_PROVIDER=ollama, OLLAMA_URL=http://host.docker.internal:11434
```
**Linux / в Docker:**
```bash
make up-local-llm                          # поднимет контейнер ollama и скачает модель
# .env: LLM_PROVIDER=ollama, OLLAMA_URL=http://ollama:11434
```
Требования: TODO(T-006) — объём памяти, время разбора одной страницы.

## Выбор модели
TODO(T-006): таблица по открытому набору (`backend/scripts/eval_extraction.py`): точность типа, точность полей,
время на документ — для локальной и облачной моделей; обоснование выбора.

## Поведение при сбое модели
Недоступность/таймаут/ошибка 5xx/429 → задание возвращается в очередь с экспоненциальной задержкой
(`JOB_MAX_ATTEMPTS`). После исчерпания попыток документ получает статус `failed` с понятной причиной, оператор может
перезапустить разбор. Документ никогда не получает «готово» без успешного ответа модели.
