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
- [claude] Stand report: Keycloak crashed — AccessDeniedException on /opt/keycloak/data/h2 (named volume is root-owned, Keycloak runs as uid 1000). Fix: removed the kcdata volume. Next to verify: realm import with ${OPERATOR_PASSWORD}, login, token accepted by backend.

## Result
Keycloak is mandatory (organizers). Token check covered by tests/test_auth.py (forged/expired/issuer/client/role).
