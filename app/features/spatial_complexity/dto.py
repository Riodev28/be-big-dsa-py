from dataclasses import dataclass
from ..reports import SpatialAnalysisReport, SpatialAiReport


@dataclass
class SpatialComplexityResponseDTO:
    analysis: SpatialAnalysisReport
    ai: SpatialAiReport | None
