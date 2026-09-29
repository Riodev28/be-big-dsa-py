from fastapi import APIRouter, status
from . import TemporalComplexityService
from . import TemporalComplexityRequest
from ...shared.cache import CacheService
from ...shared.cache.client import make_client
from ...shared.ai.service import AIService
from ...shared.ai.client import create_ai_client

router = APIRouter()

cache = CacheService(make_client())
ai = AIService(create_ai_client())

service = TemporalComplexityService(cache, ai)


@router.post("/temporal", status_code=status.HTTP_200_OK)
async def analyze(body: TemporalComplexityRequest):
    return await service.analyze(body)
