from .repository import UserRepository
from .dto import LoginDTORequest, RegisterDTORequest, LoginDTOResponse, UserResponse, RegisterDTOReponse

class UserController:
    
    def __init__(self, repository: UserRepository):
        self.respository = repository
    
    async def login(self, dto: LoginDTORequest) -> LoginDTOResponse:
        return await self.respository.login(dto)
        
    async def me(self, token: str) -> UserResponse:
        return await self.respository.me(token=token)
    
    async def register(self, dto: RegisterDTORequest) -> RegisterDTOReponse:
        return await self.respository.register(dto)