---
id: T-012
title: Keycloak + Docker stand: fix everything T-001 reports, verify OIDC end-to-end
owner: claude
status: review
prio: P0
model: opus
depends:
---
## Goal
Case 3.3 says login+password; we were told OIDC/Keycloak. Decide by questions.md A7. If Keycloak not required — consider built-in login (users table + password hash + session in DB) to cut stand risk.

## Acceptance
- [ ] decision in docs/decisions.md
- [ ] operator routes 401 without login, file URLs too

## Notes

## Thread

## Result
Keycloak is mandatory (organizers). Token check covered by tests/test_auth.py (forged/expired/issuer/client/role).
