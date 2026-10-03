from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    code: str = Field(min_length=1)
    explain_ai: bool = False
    title: str | None = Field(default=None, max_length=100)
