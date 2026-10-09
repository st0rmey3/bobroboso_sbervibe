"""Operator authentication: Keycloak access token (OIDC, Authorization Code + PKCE on the frontend).

The backend trusts nothing from the client: signature (JWKS), issuer, expiry, client (azp) and role are checked here.
"""

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

_bearer = HTTPBearer(auto_error=False)


@dataclass
class Operator:
    sub: str
    username: str
    roles: list[str]


@lru_cache
def _jwks() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(settings.oidc_jwks_url, cache_keys=True)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


def require_operator(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Operator:
    if creds is None:
        raise _unauthorized("Требуется вход")
    token = creds.credentials
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        # Keycloak access tokens have aud="account" by default; we check azp (the client) instead.
        claims = jwt.decode(
            token, key, algorithms=["RS256"], issuer=settings.oidc_issuer, options={"verify_aud": False}
        )
    except jwt.PyJWTError:
        raise _unauthorized("Недействительный или истёкший токен") from None
    if claims.get("azp") != settings.oidc_client_id:
        raise _unauthorized("Токен выдан другому клиенту")
    roles = claims.get("realm_access", {}).get("roles", [])
    if settings.operator_role not in roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет роли оператора")
    return Operator(sub=claims["sub"], username=claims.get("preferred_username", claims["sub"]), roles=roles)
