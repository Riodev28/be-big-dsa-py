import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

from .dataclasses import Claims, IssuedToken, TokenData
from .exceptions import AuthExceptions

TokenType = Literal["access", "refresh"]

bearer = HTTPBearer()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def access_token_lifetime() -> timedelta:
    return timedelta(minutes=settings.token_expire)


def refresh_token_lifetime() -> timedelta:
    return timedelta(days=settings.refresh_token_expire_days)


def _create_token(data: TokenData, token_type: TokenType, lifetime: timedelta) -> IssuedToken:
    now = datetime.now(timezone.utc)
    expires_at = now + lifetime
    jti = str(uuid.uuid4())
    payload = {
        **asdict(data),
        "type": token_type,
        "iat": now,
        "exp": expires_at,
        "jti": jti,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return IssuedToken(token=token, jti=jti, expires_at=expires_at)


def create_access_token(data: TokenData) -> str:
    return _create_token(data, "access", access_token_lifetime()).token


def create_refresh_token(data: TokenData) -> IssuedToken:
    return _create_token(data, "refresh", refresh_token_lifetime())


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """
    Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError on bad tokens,
    including a valid token of the wrong type (refresh used as access, etc).
    """
    payload = jwt.decode(
        jwt=token,
        key=settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
        options={"require": ["exp", "jti", "type"]},
    )

    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Wrong token type")

    return payload


def get_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> Claims:
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.ExpiredSignatureError:
        raise AuthExceptions.token_expired()
    except jwt.InvalidTokenError:
        raise AuthExceptions.invalid_token()

    user_id = payload.get("user_id")
    email = payload.get("email")
    if user_id is None or email is None:
        raise AuthExceptions.invalid_token()

    return Claims(
        user_id=user_id,
        username=payload.get("username", ""),
        email=email,
        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    )
