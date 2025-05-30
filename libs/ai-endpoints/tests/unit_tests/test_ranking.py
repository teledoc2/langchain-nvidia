import warnings
from typing import Any, Literal, Optional

import pytest
from langchain_core.documents import Document
from requests_mock import Mocker

from langchain_nvidia_ai_endpoints import NVIDIARerank


@pytest.fixture(autouse=True)
def mock_v1_models(requests_mock: Mocker) -> None:
    requests_mock.get(
        "https://integrate.api.nvidia.com/v1/models",
        json={
            "data": [
                {
                    "id": "mock-model",
                    "object": "model",
                    "created": 1234567890,
                    "owned_by": "OWNER",
                }
            ]
        },
    )


@pytest.fixture(autouse=True)
def mock_v1_ranking(requests_mock: Mocker) -> None:
    requests_mock.post(
        "https://integrate.api.nvidia.com/v1/ranking",
        json={
            "rankings": [
                {"index": 0, "logit": 4.2},
            ]
        },
    )


@pytest.mark.parametrize(
    "truncate",
    [
        None,
        "END",
        "NONE",
    ],
)
def test_truncate(
    requests_mock: Mocker,
    truncate: Optional[Literal["END", "NONE"]],
) -> None:
    truncate_param = {}
    if truncate:
        truncate_param = {"truncate": truncate}
    warnings.filterwarnings(
        "ignore", ".*Found mock-model in available_models.*"
    )  # expect to see this warning
    client = NVIDIARerank(api_key="BOGUS", model="mock-model", **truncate_param)
    response = client.compress_documents(
        documents=[Document(page_content="Nothing really.")], query="What is it?"
    )

    assert len(response) == 1

    assert requests_mock.last_request is not None
    request_payload = requests_mock.last_request.json()
    if truncate is None:
        assert "truncate" not in request_payload
    else:
        assert "truncate" in request_payload
        assert request_payload["truncate"] == truncate


@pytest.mark.parametrize("truncate", [True, False, 1, 0, 1.0, "START", "BOGUS"])
def test_truncate_invalid(truncate: Any) -> None:
    with pytest.raises(ValueError):
        NVIDIARerank(truncate=truncate)


def test_extra_headers(requests_mock: Mocker) -> None:
    client = NVIDIARerank(
        api_key="BOGUS", model="mock-model", extra_headers={"X-Test": "test"}
    )
    assert client.extra_headers == {"X-Test": "test"}

    _ = client.compress_documents(
        documents=[Document(page_content="Nothing really.")], query="What is it?"
    )
    assert requests_mock.last_request is not None
    assert requests_mock.last_request.headers["X-Test"] == "test"
