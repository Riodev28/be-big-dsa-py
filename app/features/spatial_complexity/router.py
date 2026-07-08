from fastapi import APIRouter, status
from ...shared.cache import CacheService, make_client
from .service import SpatialComplexityService
from .request import SpatialComplexityRequest
from ...shared.ai import AIService, create_ai_client

router = APIRouter()

cache = CacheService(make_client())
ai = AIService(create_ai_client())

service = SpatialComplexityService(cache, ai)


@router.post("/spatial", status_code=status.HTTP_200_OK)
async def analyze(body: SpatialComplexityRequest):
    return await service.analyze(body)
