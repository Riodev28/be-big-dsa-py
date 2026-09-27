from pydantic import BaseModel, EmailStr, SecretStr

class LoginDTORequest(BaseModel):
    email: EmailStr
    password: SecretStr
    
    
class LoginDTOResponse(BaseModel):
    access_token: str
    token_type: str


class RegisterDTORequest(BaseModel):
    username: str
    email: EmailStr
    password: SecretStr
    password_check: SecretStr
    
    
class RegisterDTOReponse(BaseModel):
    username: str
    email: EmailStr
    access_token: str
    token_type: str
    
    
class UserResponse(BaseModel):
    id: str | None = None
    username: str
    email: EmailStr
    
class FilesDTOResponse(BaseModel):
    code: str
    user_id: str