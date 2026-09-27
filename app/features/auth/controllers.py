from .repositories.user_repository import UserRepository
from .repositories.file_repository import FileRepository
from .schemas import ( 
    LoginDTORequest,
    RegisterDTORequest,
    LoginDTOResponse,
    UserResponse,
    RegisterDTOReponse,
    FileDTOResponse,
    FileDTOCreateRequest
)
from .dataclasses import (
    Claims,
    CreateFileRequest
)

class UserController:
    
    def __init__(self, repository: UserRepository):
        self.respository = repository
    
    async def login(self, dto: LoginDTORequest) -> LoginDTOResponse:
        return await self.respository.login(dto)
        
    async def me(self, claims: Claims) -> UserResponse:
        email: str = claims.email
        return await self.respository.me(email=email)
    
    async def register(self, dto: RegisterDTORequest) -> RegisterDTOReponse:
        return await self.respository.register(dto)
    

class FileController:
    
    def __init__(self, repository: FileRepository, user_repo: UserRepository):
        self.repository = repository
        self.user_repo = user_repo 
        
    async def index(self, user_id: str) -> list[FileDTOResponse]:
        user = self.user_repo.get_by_id(id=user_id)
        files = await self.repository.index(user=user)
        owner = UserResponse(id=user.id, username=user.username, email=user.email)

        return [
            FileDTOResponse(
                title=file.title,
                content=file.content,
                user=owner,
                created_at=file.created_at,
                updated_at=file.updated_at,
            )
            for file in files
        ]
        
    
    async def create(self, dto: FileDTOCreateRequest, user_id: str) -> FileDTOResponse:
        user = self.user_repo.get_by_id(id=user_id)
        new_file = await self.repository.save(
            request=CreateFileRequest(
                title=dto.title,
                content=dto.content,
                user=user
            ))
        owner = UserResponse(id=user.id, username=user.username, email=user.email)
        
        return FileDTOResponse(
            title=new_file.title,
            content=new_file.content,
            user=owner,
            created_at=new_file.created_at,
            updated_at=new_file.updated_at
        )
        