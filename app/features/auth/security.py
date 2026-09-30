import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any
from app.core.config import settings
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, status
from .dataclasses import Claims, TokenData
from fastapi.exceptions import HTTPException
from dataclasses import asdict
from typing import Literal
import uuid

bearer = HTTPBearer()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

TokenType = Literal["access", "refresh"]

def _create_token(data: TokenData, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        **asdict(data),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

def create_access_token(data: TokenData, expires_delta: timedelta | None = None) -> str:
    """ Create the access token for user """
    return _create_token(data=data, token_type="access", expires_delta=expires_delta or timedelta(minutes=15))


def refresh_access_token(data: TokenData, expires_delta: timedelta | None = None) -> str:
    """ Refresh the token """
    return _create_token(data=data, token_type="refresh", expires_delta=expires_delta or timedelta(minutes=15))


def time_token_expires() -> timedelta:
    return timedelta(minutes = settings.token_expire)


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    payload = jwt.decode(
        jwt=token,
        key = settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.algorithm]
    )
    
    if payload.get("type") != expected_type: raise jwt.InvalidTokenError("Wrong token type")
    
    return payload
    
    
def get_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> Claims:
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    user_id: str = payload.get("user_id")
    username: str = payload.get("username")
    email: str = payload.get("email")
    
    exp = payload.get("exp")
    if email is None or exp is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token claims")

    return Claims(
        user_id=user_id,
        username=username,
        email=email,
        expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
    )