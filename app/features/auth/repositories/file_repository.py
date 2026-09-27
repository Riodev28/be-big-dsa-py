from ..models import FileModel, UserModel
from typing import Optional

class FileRepository:
    
    async def index(self, user: UserModel) -> list[FileModel]:
        return list(FileModel.objects(owner=user))
        