from fastapi import APIRouter, status, Depends
from .controllers import (
    UserController,
    FileController
)

from .schemas import (
    LoginDTORequest,
    RegisterDTORequest,
    UserResponse,
    RegisterDTOReponse,
    LoginDTOResponse,
    FileDTOResponse,
    FileDTOCreateRequest
)

from .repositories import (
    UserRepository,
    FileRepository
)

from fastapi.security import HTTPBearer
from .security import get_claims
from .dataclasses import Claims


router = APIRouter()
security = HTTPBearer()

user_repository = UserRepository()
controller = UserController(repository=user_repository)

file_repository = FileRepository()
file_controller = FileController(repository=file_repository, user_repo=user_repository)

@router.get('/me', status_code=status.HTTP_200_OK)
async def me(claims: Claims = Depends(get_claims)) -> UserResponse:
    return await controller.me(claims=claims)


@router.post('/login', status_code=status.HTTP_200_OK)
async def login(dto: LoginDTORequest) -> LoginDTOResponse:
    return await controller.login(dto=dto)


@router.post('/register', status_code=status.HTTP_200_OK)
async def register(dto: RegisterDTORequest) -> RegisterDTOReponse:
    return await controller.register(dto=dto)


@router.get("/files", status_code=status.HTTP_200_OK)
async def files(claims: Claims = Depends(get_claims)) -> list[FileDTOResponse]:
    user_id = claims.user_id
    return await file_controller.index(user_id=user_id)


@router.post("/file", status_code=201)
async def create_files(dto: FileDTOCreateRequest, claims: Claims = Depends(get_claims)) -> FileDTOResponse:
    return await file_controller.create(dto=dto, user_id=claims.user_id)