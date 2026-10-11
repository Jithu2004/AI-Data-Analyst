from pydantic import BaseModel, Field


# =========================================================
# ANALYSIS MODELS
# =========================================================

class FilterCondition(BaseModel):
    column: str
    value: str


class AnalysisPlan(BaseModel):
    operation: str
    metric: str | None = None
    filters: list[FilterCondition] = Field(default_factory=list)
    group_by: str | None = None
    sort_direction: str | None = None
    top_n: int | None = None