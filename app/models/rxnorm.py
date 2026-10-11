from pydantic import BaseModel, Field


class RxNormCandidate(BaseModel):
    """A medication concept returned by RxNorm."""

    rxcui: str
    name: str | None = None
    score: float | None = None
    rank: int | None = None
    source: str | None = None


class RxNormSearchResponse(BaseModel):
    """Normalized result of a medication name search."""

    query: str
    candidates: list[RxNormCandidate] = Field(default_factory=list)
