from .repositories.user_repository import UserRepository
from .repositories.file_repository import FileRepository
from .schemas import ( 
    LoginDTORequest,
    RegisterDTORequest,
    LoginDTOResponse,
    UserResponse,
    RegisterDTOReponse,
    FilesDTOResponse
)
from .dataclasses import Claims
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
        
    async def index(self, user_id: str) -> list[FilesDTOResponse]:
        user = self.user_repo.get_by_id(id=user_id)
        return await self.repository.index(user=user)