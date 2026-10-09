.PHONY: up up-local-llm down logs ps reset test openapi board

up:
	docker compose up -d --build

up-local-llm:
	docker compose --profile local-llm up -d --build
	docker compose exec ollama ollama pull $${OLLAMA_MODEL:-qwen2.5vl:7b}

down:
	docker compose down

logs:
	docker compose logs -f --tail=100 $(s)

ps:
	docker compose ps

reset:
	docker compose down -v

test:
	docker compose exec backend pytest -q

openapi:
	docker compose exec backend python scripts/export_openapi.py > docs/api/openapi.json

board:
	scripts/board.sh
