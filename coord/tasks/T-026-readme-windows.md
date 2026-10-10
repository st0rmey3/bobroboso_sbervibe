---
id: T-026
title: README: Windows/PowerShell notes + troubleshooting (Keycloak, proxy, Ollama on CPU)
owner: claude
status: todo
prio: P1
model: sonnet
depends:
---
## Goal
Everything the stand owner hit today goes into README «Если что-то не работает»: Keycloak page error → check `docker compose logs keycloak`; venue proxy → NO_PROXY lines; `restart` doesn't re-read .env → `up -d`; Ollama shows 100% CPU → stop the docker ollama container, use native Ollama, qwen2.5vl:3b; acceptance run command. PowerShell equivalents where they differ (`copy` vs `cp`, `findstr`).

## Acceptance
- [ ] a stranger on Windows can follow README from zero
- [ ] no TODO left in docs/

## Notes

## Thread

## Result
