import httpx

from app.models.rxnorm import RxNormCandidate, RxNormSearchResponse

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"


class RxNormServiceError(Exception):
    """Raised when RxNorm cannot provide a usable response."""


async def search_rxnorm_medications(
    term: str,
    max_entries: int = 10,
    client: httpx.AsyncClient | None = None,
) -> RxNormSearchResponse:
    """Search medication concepts using the official RxNorm API."""

    normalized_term = term.strip()
    if not normalized_term:
        raise ValueError("Medication search term must not be empty.")

    if not 1 <= max_entries <= 20:
        raise ValueError("max_entries must be between 1 and 20.")

    params = {
        "term": normalized_term,
        "maxEntries": max_entries,
        "option": 1,
    }
    owns_client = client is None

    try:
        if owns_client:
            client = httpx.AsyncClient(
                base_url=RXNORM_BASE_URL,
                timeout=10.0,
            )

        assert client is not None
        response = await client.get(
            "/approximateTerm.json",
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

    except httpx.TimeoutException as exc:
        raise RxNormServiceError("RxNorm request timed out.") from exc
    except httpx.HTTPError as exc:
        raise RxNormServiceError("RxNorm request failed.") from exc
    except ValueError as exc:
        raise RxNormServiceError("RxNorm returned an invalid response.") from exc
    finally:
        if owns_client and client is not None:
            await client.aclose()

    group = payload.get("approximateGroup") or {}
    raw_candidates = group.get("candidate") or []

    if isinstance(raw_candidates, dict):
        raw_candidates = [raw_candidates]

    candidates = [
        RxNormCandidate(
            rxcui=item["rxcui"],
            name=item.get("name"),
            score=(float(item["score"]) if item.get("score") is not None else None),
            rank=(int(item["rank"]) if item.get("rank") is not None else None),
            source=item.get("source"),
        )
        for item in raw_candidates
        if isinstance(item, dict) and item.get("rxcui")
    ]

    return RxNormSearchResponse(
        query=normalized_term,
        candidates=candidates,
    )
