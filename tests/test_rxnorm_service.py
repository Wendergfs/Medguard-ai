import asyncio

import httpx
import pytest

from app.services.rxnorm_service import (
    RxNormServiceError,
    search_rxnorm_medications,
)


def test_search_returns_rxnorm_candidates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/REST/approximateTerm.json"
        assert request.url.params["term"] == "aspirin"
        return httpx.Response(
            200,
            json={
                "approximateGroup": {
                    "candidate": [
                        {
                            "rxcui": "1191",
                            "name": "aspirin 325 MG Oral Tablet",
                            "score": "10.0",
                            "rank": "1",
                            "source": "RXNORM",
                        }
                    ]
                }
            },
        )

    async def run_test():
        async with httpx.AsyncClient(
            base_url="https://rxnav.nlm.nih.gov/REST",
            transport=httpx.MockTransport(handler),
        ) as client:
            return await search_rxnorm_medications(
                " aspirin ",
                client=client,
            )

    result = asyncio.run(run_test())

    assert result.query == "aspirin"
    assert len(result.candidates) == 1
    assert result.candidates[0].rxcui == "1191"
    assert result.candidates[0].rank == 1


def test_search_returns_empty_list_when_no_match() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"approximateGroup": {}},
        )

    async def run_test():
        async with httpx.AsyncClient(
            base_url="https://rxnav.nlm.nih.gov/REST",
            transport=httpx.MockTransport(handler),
        ) as client:
            return await search_rxnorm_medications(
                "unknown medication",
                client=client,
            )

    result = asyncio.run(run_test())
    assert result.candidates == []


def test_search_raises_error_on_http_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async def run_test():
        async with httpx.AsyncClient(
            base_url="https://rxnav.nlm.nih.gov/REST",
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(RxNormServiceError):
                await search_rxnorm_medications(
                    "aspirin",
                    client=client,
                )

    asyncio.run(run_test())


def test_search_rejects_blank_term() -> None:
    with pytest.raises(ValueError):
        asyncio.run(search_rxnorm_medications("   "))


def test_search_rejects_invalid_max_entries() -> None:
    with pytest.raises(ValueError):
        asyncio.run(search_rxnorm_medications("aspirin", max_entries=0))
