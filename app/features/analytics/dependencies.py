from typing import Annotated

from fastapi import Depends

from .repository import AnalysisRecordRepository
from .services import AnalysisHistoryService, DashboardService

# Composition root for the feature: the only place that picks implementations.
# Tests swap them with `app.dependency_overrides[get_dashboard_service] = ...`
_repository = AnalysisRecordRepository()
_dashboard_service = DashboardService(_repository)
_history_service = AnalysisHistoryService(_repository)


def get_dashboard_service() -> DashboardService:
    return _dashboard_service


def get_history_service() -> AnalysisHistoryService:
    return _history_service


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
HistoryServiceDep = Annotated[AnalysisHistoryService, Depends(get_history_service)]
