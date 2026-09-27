from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..schemas import LoginDTORequest, RegisterDTORequest, UserResponse, LoginDTOResponse, RegisterDTOReponse
from ..security import *
from ..exceptions import AuthExceptions
from ..models import UserModel
from ..dataclasses import TokenData

class UserRepository:

    oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

    
    def get_by_email(self,email: str) -> str|None:
        return UserModel.objects(email=email).first()
    
    
    async def register(self, credentials: RegisterDTORequest) -> RegisterDTOReponse:
        user_exists = self.get_by_email(email = credentials.email)
        
        if user_exists is not None: AuthExceptions.user_exists()

        new_user = await self.create(credentials=credentials)
        
        access_token = create_access_token(
            data = TokenData(
                user_id= str(new_user.id),
                username= new_user.username,
                email= new_user.email,
            ),
            expires_delta=time_token_expires()
        )
        
        return RegisterDTOReponse(
            username=new_user.username,
            email=new_user.email,
            access_token=access_token,
            token_type="bearer"
        )    
            
    async def login(self, credentials: LoginDTORequest) -> LoginDTOResponse:        
        user = self.get_by_email(email = credentials.email)

        if not user or not verify_password(plain = credentials.password.get_secret_value(), hashed = user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data = TokenData(
                user_id=str(user["id"]),
                username=user["username"],
                email=user["email"]
            ),
            expires_delta=time_token_expires()
        )
        
        return LoginDTOResponse(
            access_token=access_token,
            token_type="bearer"
        )        
        
    async def me(self, email: str) -> UserResponse:
            
        if email is None:
            raise AuthExceptions.credentials_exceptions()
        
        user: UserModel = UserModel.objects.get(email=email)
        
        if user is None:
            raise AuthExceptions.credentials_exceptions()
        
        return UserResponse(
            username=user.username,
            email=user.email
        )
    
    
    async def create(self, credentials: RegisterDTORequest) -> UserResponse:
        user = UserModel(
            username=credentials.username,
            email=credentials.email,
            password=hash_password(password=credentials.password.get_secret_value())
        ).save()
                
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email
        )