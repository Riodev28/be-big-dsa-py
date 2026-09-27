from pydantic import BaseModel, EmailStr, SecretStr, field_validator
from datetime import datetime

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
    
    @field_validator("id", mode="before")
    @classmethod
    def objectid_to_str(cls, v):
        return str(v) if v is not None else v
    
class FileDTOResponse(BaseModel):
    title: str
    content: str
    user: UserResponse
    created_at: datetime
    updated_at: datetime | None = None
    
    
class FileDTOCreateRequest(BaseModel):
    title: str
    content: str
