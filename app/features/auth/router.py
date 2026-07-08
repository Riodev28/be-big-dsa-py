from fastapi import APIRouter, status, Depends
from . import (
    UserController,
    LoginDTORequest,
    RegisterDTORequest,
    UserRepository,
    UserResponse,
    RegisterDTOReponse,
    LoginDTOResponse
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter()
security = HTTPBearer()

repository = UserRepository()
controller = UserController(repository=repository)

@router.get('/me', status_code=status.HTTP_200_OK)
async def me(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    token = credentials.credentials
    return await controller.me(token=token)


@router.post('/login', status_code=status.HTTP_200_OK)
async def login(dto: LoginDTORequest) -> LoginDTOResponse:
    return await controller.login(dto=dto)


@router.post('/register', status_code=status.HTTP_200_OK)
async def register(dto: RegisterDTORequest) -> RegisterDTOReponse:
    return await controller.register(dto=dto)