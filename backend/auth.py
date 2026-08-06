"""
Verifies the JWT that Supabase issues when a user logs in via supabase-js
on the frontend.

Since October 2025, Supabase signs new projects' user session tokens with
an asymmetric key (ES256), verified against a public JWKS endpoint —
NOT a shared secret. This is why a plain HS256-with-shared-secret approach
fails on current projects with "Invalid auth token" / "Invalid signature".

PyJWT needs the `cryptography` package to even support ES256 at all — see
requirements.txt (`pyjwt[crypto]`). Without it, you'd hit:
    AttributeError: module 'jwt.algorithms' has no attribute 'ECAlgorithm'

We use PyJWT's PyJWKClient, which fetches and caches the project's public
keys from:
    https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
and picks the right one automatically based on the token's `kid` header.

Older projects that haven't migrated still sign with HS256 + a shared
secret — if you set SUPABASE_JWT_SECRET, we fall back to that when a token
isn't verifiable via JWKS (e.g. the JWKS endpoint returns no keys at all,
which is what happens on a legacy-only project).
"""
from fastapi import Header, HTTPException
import jwt
from jwt import PyJWKClient

from config import SUPABASE_URL, SUPABASE_JWT_SECRET

_jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json", cache_keys=True) if SUPABASE_URL else None


def _verify_via_jwks(token: str) -> dict:
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated")


def _verify_via_legacy_secret(token: str) -> dict:
    return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: add `user: dict = Depends(get_current_user)` to any protected route."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
    token = authorization[len("Bearer "):]

    payload = None
    jwks_error = None
    if _jwks_client:
        try:
            payload = _verify_via_jwks(token)
        except Exception as e:
            jwks_error = e

    if payload is None and SUPABASE_JWT_SECRET:
        try:
            payload = _verify_via_legacy_secret(token)
        except Exception as e:
            jwks_error = jwks_error or e

    if payload is None:
        if isinstance(jwks_error, jwt.ExpiredSignatureError):
            raise HTTPException(status_code=401, detail="Token expired, please log in again")
        raise HTTPException(status_code=401, detail="Invalid auth token")

    return {"id": payload["sub"], "email": payload.get("email")}
