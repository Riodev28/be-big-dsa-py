import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any
from ...core.config import settings
    
def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Create the access token for user """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
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