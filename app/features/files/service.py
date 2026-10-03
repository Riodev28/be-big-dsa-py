from app.features.auth.models import UserModel
from app.shared.ai.naming import AlgorithmNamer, NullAlgorithmNamer

from .exceptions import FileExceptions
from .models import FileModel
from .repository import FileRepository
from .schemas import FileDTOCreateRequest, FileDTOUpdateRequest


class FileService:
    """File use cases, always scoped to the owner so users only see their own files."""

    def __init__(self, repository: FileRepository, namer: AlgorithmNamer | None = None):
        self.repository = repository
        self.namer = namer or NullAlgorithmNamer()

    def list_files(self, owner: UserModel) -> list[FileModel]:
        return self.repository.list_by_owner(owner)

    def get(self, id: str, owner: UserModel) -> FileModel:
        file = self.repository.get_by_id(id, owner)
        if file is None:
            raise FileExceptions.not_found()
        return file

    def create(self, dto: FileDTOCreateRequest, owner: UserModel) -> FileModel:
        return self.repository.create(
            title=dto.title,
            algorithm_name=self.namer.name(dto.content),
            content=dto.content,
            owner=owner,
        )

    def update(self, id: str, dto: FileDTOUpdateRequest, owner: UserModel) -> FileModel:
        file = self.get(id, owner)
        # Only ask the AI again when the code changed or there is no name yet
        algorithm_name = (
            file.algorithm_name
            if dto.content == file.content and file.algorithm_name
            else self.namer.name(dto.content)
        )
        return self.repository.update(
            file,
            title=dto.title,
            algorithm_name=algorithm_name,
            content=dto.content,
        )

    def delete(self, id: str, owner: UserModel) -> None:
        self.repository.delete(self.get(id, owner))
