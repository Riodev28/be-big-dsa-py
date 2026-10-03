from fastapi import APIRouter, status
from ...shared.cache import CacheService, make_client
from .service import SpatialComplexityService
from .request import SpatialComplexityRequest
from ..analytics.recorder import MongoAnalysisRecorder
from ..auth.dependencies import OptionalClaims
from ...shared.ai import AIService, create_ai_client
from ...shared.ai.naming import AIAlgorithmNamer

router = APIRouter()

cache = CacheService(make_client())
ai = AIService(create_ai_client())

service = SpatialComplexityService(
    cache, ai, recorder=MongoAnalysisRecorder(), namer=AIAlgorithmNamer(ai)
)


@router.post("/spatial", status_code=status.HTTP_200_OK)
async def analyze(body: SpatialComplexityRequest, claims: OptionalClaims):
    return await service.analyze(body, user_id=claims.user_id if claims else None)
