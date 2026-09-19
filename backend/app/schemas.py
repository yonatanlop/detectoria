from pydantic import BaseModel, Field


class SourceResult(BaseModel):
    id: str
    name: str
    score: int = Field(ge=0, le=100, description="0-100 probability text is AI-generated")
    label: str
    weight: float
    details: str


class AnalyzeResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    label: str
    sources: list[SourceResult]
    warnings: list[str] = []
    disclaimer: str


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    translation_classifier_enabled: bool


class ErrorResponse(BaseModel):
    detail: str
