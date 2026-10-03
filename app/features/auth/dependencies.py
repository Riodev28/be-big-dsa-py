from typing import Annotated

from fastapi import Depends

from .dataclasses import Claims
from .models import UserModel
from .repositories import RefreshTokenRepository, UserRepository
from .security import get_claims
from .services import AuthService

auth_service = AuthService(users=UserRepository(), refresh_tokens=RefreshTokenRepository())


def get_auth_service() -> AuthService:
    return auth_service


def get_current_user(
    claims: Claims = Depends(get_claims),
    service: AuthService = Depends(get_auth_service),
) -> UserModel:
    return service.get_current_user(claims.user_id)


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
