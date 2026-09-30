from fastapi import APIRouter, status, Depends, Response, Cookie
from .controllers import (
    UserController,
    FileController
)

from .schemas import (
    LoginDTORequest,
    RegisterDTORequest,
    UserResponse,
    RegisterDTOReponse,
    RefreshTokenDTOResponse,
    LoginDTOResponse,
    FileDTOResponse,
    FileDTOCreateRequest,
    FileDTOUpdateRequest
)

from .repositories import (
    UserRepository,
    FileRepository
)

from fastapi.security import HTTPBearer
from fastapi.exceptions import HTTPException
from .security import get_claims
from .dataclasses import Claims


router = APIRouter()
security = HTTPBearer()

user_repository = UserRepository()
controller = UserController(repository=user_repository)

file_repository = FileRepository()
file_controller = FileController(repository=file_repository, user_repo=user_repository)

# ==========================================================================================
# Auth endpoints
# ==========================================================================================

@router.get('/me', status_code=status.HTTP_200_OK)
async def me(claims: Claims = Depends(get_claims)) -> UserResponse:
    return await controller.me(claims=claims)


@router.post('/login', status_code=status.HTTP_200_OK)
async def login(dto: LoginDTORequest) -> LoginDTOResponse:
    return await controller.login(dto=dto)


@router.post('/register', status_code=status.HTTP_200_OK)
async def register(dto: RegisterDTORequest) -> RegisterDTOReponse:
    return await controller.register(dto=dto)

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(response: Response,
    refresh_token: str | None = Cookie(default=None),) -> RefreshTokenDTOResponse:
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")

    result = await controller.refresh(refresh_token=refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/auth/refresh",
        max_age=7 * 24 * 3600,
    )
    return RefreshTokenDTOResponse(access_token=result.access_token)

# ==========================================================================================
# Files endpoints
# ==========================================================================================

@router.get("/files", status_code=status.HTTP_200_OK)
async def files(claims: Claims = Depends(get_claims)) -> list[FileDTOResponse]:
    user_id = claims.user_id
    return await file_controller.index(user_id=user_id)


@router.get("/file/{id}", status_code=status.HTTP_200_OK)
async def get_file(id: str, claims: Claims = Depends(get_claims)) -> FileDTOResponse:
    return await file_controller.detail(id=id, user_id=claims.user_id)


@router.post("/file", status_code=status.HTTP_201_CREATED)
async def create_file(dto: FileDTOCreateRequest, claims: Claims = Depends(get_claims)) -> FileDTOResponse:
    return await file_controller.create(dto=dto, user_id=claims.user_id)


@router.put("/file/{id}", status_code=status.HTTP_202_ACCEPTED)
async def update_file(id: str, dto: FileDTOUpdateRequest, claims: Claims = Depends(get_claims)) -> FileDTOResponse:
    return await file_controller.update(id=id, dto=dto, user_id=claims.user_id)


@router.delete("/file/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(id: str, claims: Claims = Depends(get_claims)) -> None:
    await file_controller.delete(id=id, user_id=claims.user_id)