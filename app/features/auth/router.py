from fastapi import APIRouter, Cookie, Response, status

from .dependencies import AuthServiceDep, CurrentUser
from .exceptions import AuthExceptions
from .schemas import (
    LoginDTORequest,
    LoginDTOResponse,
    RefreshTokenDTOResponse,
    RegisterDTORequest,
    RegisterDTOResponse,
    UserResponse,
)
from .security import refresh_token_lifetime

# Handlers are sync on purpose: mongoengine blocks, so FastAPI runs them in
# its threadpool instead of stalling the event loop.

router = APIRouter()

REFRESH_COOKIE = "refresh_token"
# Must cover the mounted /refresh and /logout routes (router lives under /api)
REFRESH_COOKIE_PATH = "/api"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
        max_age=int(refresh_token_lifetime().total_seconds()),
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=True,
        samesite="strict",
    )


@router.get("/me", status_code=status.HTTP_200_OK)
def me(user: CurrentUser) -> UserResponse:
    return UserResponse(id=user.id, username=user.username, email=user.email)


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    dto: LoginDTORequest, response: Response, service: AuthServiceDep
) -> LoginDTOResponse:
    tokens = service.login(dto)
    _set_refresh_cookie(response, tokens.refresh_token)
    return LoginDTOResponse(access_token=tokens.access_token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    dto: RegisterDTORequest, response: Response, service: AuthServiceDep
) -> RegisterDTOResponse:
    user, tokens = service.register(dto)
    _set_refresh_cookie(response, tokens.refresh_token)
    return RegisterDTOResponse(
        username=user.username,
        email=user.email,
        access_token=tokens.access_token,
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(
    response: Response,
    service: AuthServiceDep,
    refresh_token: str | None = Cookie(default=None),
) -> RefreshTokenDTOResponse:
    if not refresh_token:
        raise AuthExceptions.missing_refresh_token()

    tokens = service.refresh(refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token)
    return RefreshTokenDTOResponse(access_token=tokens.access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    service: AuthServiceDep,
    refresh_token: str | None = Cookie(default=None),
) -> None:
    if refresh_token:
        service.logout(refresh_token)
    _clear_refresh_cookie(response)
