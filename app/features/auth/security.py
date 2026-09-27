import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any
from app.core.config import settings
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, status
from .dataclasses import Claims
from fastapi.exceptions import HTTPException

bearer = HTTPBearer()

_now: datetime = datetime.now(timezone.utc) 

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Create the access token for user """
    to_encode = data.copy()
    expire = _now + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    
    return jwt.encode(
        payload = to_encode,
        key = settings.jwt_secret_key,
        algorithm = settings.algorithm)


def time_token_expires() -> timedelta:
    return timedelta(minutes = settings.token_expire)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        jwt=token,
        key = settings.jwt_secret_key,
        algorithms=[settings.algorithm]
    )
    
def get_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> Claims:
    try:
        payload = decode_token(credentials.credentials)  # already checks exp
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    email = payload.get("sub")
    exp = payload.get("exp")
    if email is None or exp is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token claims")

    return Claims(
        email=email,
        expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
    )