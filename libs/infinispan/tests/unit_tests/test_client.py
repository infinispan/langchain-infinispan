from unittest.mock import MagicMock

import pytest

from langchain_infinispan.client import InfinispanClient


@pytest.fixture
def client() -> InfinispanClient:
    c = InfinispanClient(url="http://localhost:11222")
    c._session = MagicMock()
    return c


@pytest.mark.parametrize(
    "status_code, expected",
    [
        # Infinispan returns 204 (No Content) for HEAD on an existing cache.
        (204, True),
        (200, True),
        (404, False),
        (401, False),
    ],
)
def test_cache_exists_accepts_2xx(
    client: InfinispanClient, status_code: int, expected: bool
) -> None:
    response = MagicMock()
    response.status_code = status_code
    response.ok = 200 <= status_code < 300
    client._session.head.return_value = response

    assert client.cache_exists("my_cache") is expected
    client._session.head.assert_called_once_with(
        "http://localhost:11222/rest/v2/caches/my_cache",
        verify=True,
    )
