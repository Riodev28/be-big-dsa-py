from ..models import FileModel, UserModel
from ..dataclasses import CreateFileRequest

class FileRepository:
    
    async def index(self, user: UserModel) -> list[FileModel]:
        return list(FileModel.objects(owner=user))
    

    async def save(self, request: CreateFileRequest) -> FileModel:
        return FileModel(title = request.title, content = request.content, owner = request.user).save()
        