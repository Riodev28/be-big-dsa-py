from pydantic import BaseModel, EmailStr, SecretStr, field_validator, model_validator

from app.shared.types import ObjectIdStr


class LoginDTORequest(BaseModel):
    email: EmailStr
    password: SecretStr


class RegisterDTORequest(BaseModel):
    username: str
    email: EmailStr
    password: SecretStr
    password_check: SecretStr

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterDTORequest":
        if self.password.get_secret_value() != self.password_check.get_secret_value():
            raise ValueError("Passwords do not match")
        return self


class TokenDTOResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginDTOResponse(TokenDTOResponse):
    pass


class RefreshTokenDTOResponse(TokenDTOResponse):
    pass


class RegisterDTOResponse(TokenDTOResponse):
    username: str
    email: EmailStr


class UserResponse(BaseModel):
    id: ObjectIdStr | None = None
    username: str
    email: EmailStr

    @field_validator("id", mode="before")
    @classmethod
    def objectid_to_str(cls, v):
        return str(v) if v is not None else v
