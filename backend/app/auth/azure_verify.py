# app/auth/azure_verify.py
import json
import jwt
import httpx
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException
from app.config import settings

_cached_jwks: dict | None = None


async def _fetch_jwks() -> dict:
    global _cached_jwks
    if _cached_jwks:
        return _cached_jwks

    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.azure_ad_jwks_url, timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Azure JWKS")
    _cached_jwks = resp.json()
    return _cached_jwks


async def verify_azure_token(id_token: str) -> dict:
    """
    Verify Azure AD ID token signature & claims.
    Returns decoded payload if valid, else raises HTTPException.
    """
    jwks = await _fetch_jwks()
    try:
        header = jwt.get_unverified_header(id_token)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token header")

    kid = header.get("kid")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if not key:
        raise HTTPException(status_code=401, detail="No matching JWK key found")

    # RSAAlgorithm.from_jwk expects a JSON string
    public_key = RSAAlgorithm.from_jwk(json.dumps(key))

    try:
        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.azure_ad_client_id,
            issuer=f"https://login.microsoftonline.com/{settings.azure_ad_tenant_id}/v2.0",
        )
        print(payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Azure token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Azure token: {e}")

    return payload
