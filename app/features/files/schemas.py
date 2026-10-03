from datetime import datetime

from pydantic import BaseModel, Field

from app.features.auth.models import UserModel
from app.features.auth.schemas import UserResponse
from app.shared.types import ObjectIdStr

from .models import FileModel


class FileDTOCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str


class FileDTOUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str


class FileDTOResponse(BaseModel):
    id: ObjectIdStr | None = None
    title: str
    content: str
    user: UserResponse
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_model(cls, file: FileModel, owner: UserModel) -> "FileDTOResponse":
        return cls(
            id=file.id,
            title=file.title,
            content=file.content,
            user=UserResponse(id=owner.id, username=owner.username, email=owner.email),
            created_at=file.created_at,
            updated_at=file.updated_at,
        )
