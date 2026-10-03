from bson import ObjectId

from app.features.auth.models import UserModel

from .models import FileModel


class FileRepository:

    def list_by_owner(self, owner: UserModel) -> list[FileModel]:
        return list(FileModel.objects(owner=owner))

    def get_by_id(self, id: str, owner: UserModel) -> FileModel | None:
        if not ObjectId.is_valid(id):
            return None
        return FileModel.objects(id=id, owner=owner).first()

    def create(self, title: str, content: str, owner: UserModel) -> FileModel:
        return FileModel(title=title, content=content, owner=owner).save()

    def update(self, file: FileModel, title: str, content: str) -> FileModel:
        file.title = title
        file.content = content
        return file.save()

    def delete(self, file: FileModel) -> None:
        file.delete()
