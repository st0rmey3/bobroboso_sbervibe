---
id: T-001
title: Stand up the whole stack end-to-end
owner: claude
status: todo
prio: P0
depends: 
---
## Goal
Run `make up` on a machine with Docker, fix whatever breaks in the skeleton (it was only unit/smoke-tested without Docker).

## Acceptance
- [ ] `docker compose up` from clean clone + `.env` works (Д1)
- [ ] Keycloak login at /operator works with user `operator`
- [ ] upload → worker → status changes visible via API
- [ ] `curl localhost:8000/api/operator/applications` without token → 401
- [ ] `make reset && make up` documented in README

## Notes
Watch: Keycloak `${OPERATOR_PASSWORD}` placeholder in realm import; issuer must equal OIDC_ISSUER.

## Thread

## Result
