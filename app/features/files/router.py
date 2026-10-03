from fastapi import APIRouter, status

from app.features.auth.dependencies import CurrentUser
from app.shared.ai.client import create_ai_client
from app.shared.ai.service import AIService

from .naming import AIAlgorithmNamer
from .repository import FileRepository
from .schemas import FileDTOCreateRequest, FileDTOResponse, FileDTOUpdateRequest
from .service import FileService

# Sync handlers: mongoengine and the naming AI call block, so FastAPI runs
# them in its threadpool.

router = APIRouter()
service = FileService(
    repository=FileRepository(),
    namer=AIAlgorithmNamer(AIService(create_ai_client())),
)


@router.get("/files", status_code=status.HTTP_200_OK)
def list_files(user: CurrentUser) -> list[FileDTOResponse]:
    return [FileDTOResponse.from_model(file, user) for file in service.list_files(user)]


@router.get("/file/{id}", status_code=status.HTTP_200_OK)
def get_file(id: str, user: CurrentUser) -> FileDTOResponse:
    return FileDTOResponse.from_model(service.get(id, user), user)


@router.post("/file", status_code=status.HTTP_201_CREATED)
def create_file(dto: FileDTOCreateRequest, user: CurrentUser) -> FileDTOResponse:
    return FileDTOResponse.from_model(service.create(dto, user), user)


@router.put("/file/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_file(
    id: str, dto: FileDTOUpdateRequest, user: CurrentUser
) -> FileDTOResponse:
    return FileDTOResponse.from_model(service.update(id, dto, user), user)


@router.delete("/file/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(id: str, user: CurrentUser) -> None:
    service.delete(id, user)
