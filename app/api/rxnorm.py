from fastapi import APIRouter, HTTPException, Query

from app.models.rxnorm import RxNormSearchResponse
from app.services.rxnorm_service import (
    RxNormServiceError,
    search_rxnorm_medications,
)

router = APIRouter(prefix="/api/v1/rxnorm", tags=["RxNorm"])


@router.get("/search", response_model=RxNormSearchResponse)
async def search_medications(
    term: str = Query(min_length=2, max_length=200),
    max_entries: int = Query(default=10, ge=1, le=20),
) -> RxNormSearchResponse:
    """Find approximate RxNorm matches for a medication name."""

    try:
        return await search_rxnorm_medications(
            term=term,
            max_entries=max_entries,
        )
    except RxNormServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="Medication terminology service is unavailable.",
        ) from exc
