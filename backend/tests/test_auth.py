"""require_operator must reject anything but a properly signed Keycloak token for our client with role operator."""

import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app import auth
from app.config import settings

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def fake_jwks(monkeypatch):
    jwks = SimpleNamespace(get_signing_key_from_jwt=lambda _t: SimpleNamespace(key=KEY.public_key()))
    monkeypatch.setattr(auth, "_jwks", lambda: jwks)


def token(key=KEY, **over):
    claims = {
        "iss": settings.oidc_issuer,
        "azp": settings.oidc_client_id,
        "sub": "u1",
        "preferred_username": "operator",
        "realm_access": {"roles": ["operator"]},
        "exp": int(time.time()) + 300,
    } | over
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=jwt.encode(claims, key, algorithm="RS256"))


def status_of(creds):
    try:
        auth.require_operator(creds)
    except HTTPException as e:
        return e.status_code
    return 200


def test_valid_operator_token():
    assert auth.require_operator(token()).username == "operator"


@pytest.mark.parametrize(
    "creds,expected",
    [
        (None, 401),
        (token(key=OTHER), 401),  # forged signature
        (token(exp=int(time.time()) - 10), 401),  # expired
        (token(iss="http://evil/realms/docs"), 401),
        (token(azp="other-client"), 401),
        (token(realm_access={"roles": []}), 403),
    ],
)
def test_rejected_tokens(creds, expected):
    assert status_of(creds) == expected
