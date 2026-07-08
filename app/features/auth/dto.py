from pydantic import BaseModel

class LoginDTORequest(BaseModel):
    email: str
    password: str
    
    
class LoginDTOResponse(BaseModel):
    access_token: str
    token_type: str


class RegisterDTORequest(BaseModel):
    username: str
    email: str
    password: str
    password_check: str
    
    
class RegisterDTOReponse(BaseModel):
    username: str
    email: str
    access_token: str
    token_type: str
    
    
class UserResponse(BaseModel):
    username: str
    email: str
