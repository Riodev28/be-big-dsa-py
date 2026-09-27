from ..models import FileModel, UserModel
from ..dataclasses import CreateFileRequest
from bson import ObjectId
from ..exceptions import FileExceptions

class FileRepository:
    
    async def index(self, user: UserModel) -> list[FileModel]:
        return list(FileModel.objects(owner=user))
    
    
    async def get_by_id(self, id: str, user: UserModel) -> FileModel:
        if not ObjectId.is_valid(id):
            raise FileExceptions.not_found()
                
        file = FileModel.objects(id=id, owner=user).first()
                
        if file is None:
            raise FileExceptions.not_found()
                
        return file
    

    async def save(self, request: CreateFileRequest) -> FileModel:
        return FileModel(title = request.title, content = request.content, owner = request.user).save()
        