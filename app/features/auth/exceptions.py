from fastapi import HTTPException, status

BEARER_HEADER = {"WWW-Authenticate": "Bearer"}


class AuthExceptions:
    """Factories for auth errors. Usage: `raise AuthExceptions.not_found()`."""

    @staticmethod
    def credentials_exceptions() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers=BEARER_HEADER,
        )

    @staticmethod
    def invalid_credentials() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers=BEARER_HEADER,
        )

    @staticmethod
    def token_expired() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers=BEARER_HEADER,
        )

    @staticmethod
    def invalid_token() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers=BEARER_HEADER,
        )

    @staticmethod
    def missing_refresh_token() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    @staticmethod
    def user_exists() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already exists",
        )

    @staticmethod
    def not_found() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
