from typing import Annotated

from fastapi import APIRouter, Query, status

from app.features.auth.dependencies import CurrentClaims
from app.shared.analysis import AnalysisKind

from .dependencies import DashboardServiceDep, HistoryServiceDep
from .schemas import (
    AnalysisDetailResponse,
    AnalysisPage,
    ComplexityTrendsResponse,
    DashboardSummaryResponse,
)

# Sync handlers: mongoengine blocks, so FastAPI runs them in its threadpool.

router = APIRouter(tags=["analytics"])

# Time and space notations measure different things, so a dashboard never
# mixes them; temporal is what the dashboard shows by default.
KindQuery = Annotated[AnalysisKind, Query()]


@router.get("/dashboard/summary", status_code=status.HTTP_200_OK)
def dashboard_summary(
    claims: CurrentClaims,
    service: DashboardServiceDep,
    kind: KindQuery = AnalysisKind.TEMPORAL,
) -> DashboardSummaryResponse:
    return service.summary(claims.user_id, kind)


@router.get("/dashboard/trends", status_code=status.HTTP_200_OK)
def dashboard_trends(
    claims: CurrentClaims,
    service: DashboardServiceDep,
    kind: KindQuery = AnalysisKind.TEMPORAL,
    months: Annotated[int, Query(ge=1, le=24)] = 6,
) -> ComplexityTrendsResponse:
    return service.trends(claims.user_id, kind, months)


@router.get("/analyses", status_code=status.HTTP_200_OK)
def list_analyses(
    claims: CurrentClaims,
    service: HistoryServiceDep,
    kind: Annotated[AnalysisKind | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalysisPage:
    return service.list_page(claims.user_id, kind, limit, offset)


@router.get("/analyses/{id}", status_code=status.HTTP_200_OK)
def get_analysis(
    id: str, claims: CurrentClaims, service: HistoryServiceDep
) -> AnalysisDetailResponse:
    return service.get(id, claims.user_id)
