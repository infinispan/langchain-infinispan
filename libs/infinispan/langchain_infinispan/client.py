import json
import logging
from typing import Any, Dict, List, Optional

import requests

from langchain_infinispan._utilities import user_agent

logger = logging.getLogger(__name__)


class _DigestAuth(requests.auth.HTTPDigestAuth):
    pass


class _BearerAuth(requests.auth.AuthBase):
    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class InfinispanClient:
    """REST client for Infinispan server."""

    def __init__(
        self,
        *,
        url: str = "http://localhost:11222",
        username: Optional[str] = None,
        password: Optional[str] = None,
        bearer_token: Optional[str] = None,
        verify: bool = True,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._base_url = url.rstrip("/")
        self._verify = verify
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent()
        if headers:
            self._session.headers.update(headers)

        if bearer_token:
            self._session.auth = _BearerAuth(bearer_token)
        elif username and password:
            self._session.auth = _DigestAuth(username, password)

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def cache_exists(self, cache_name: str) -> bool:
        r = self._session.head(
            self._url(f"/rest/v2/caches/{cache_name}"),
            verify=self._verify,
        )
        # Infinispan answers HEAD on an existing cache with 204 (No Content),
        # not 200, so treat any 2xx success status as "exists". Checking only
        # for 200 made cache_exists() always return False, so get_or_create_cache
        # would try to re-create an existing cache and fail with HTTP 400
        # (ISPN000507: Cache already exists).
        return r.ok

    def create_cache(self, cache_name: str, config: str) -> None:
        r = self._session.post(
            self._url(f"/rest/v2/caches/{cache_name}"),
            data=config,
            headers={"Content-Type": "application/xml"},
            verify=self._verify,
        )
        r.raise_for_status()
        logger.info("Created cache %s", cache_name)

    def get_or_create_cache(self, cache_name: str, config: str) -> None:
        if not self.cache_exists(cache_name):
            self.create_cache(cache_name, config)

    def delete_cache(self, cache_name: str) -> None:
        r = self._session.delete(
            self._url(f"/rest/v2/caches/{cache_name}"),
            verify=self._verify,
        )
        r.raise_for_status()

    def clear_cache(self, cache_name: str) -> None:
        r = self._session.post(
            self._url(f"/rest/v2/caches/{cache_name}?action=clear"),
            verify=self._verify,
        )
        r.raise_for_status()

    def put(self, cache_name: str, key: str, value: Any) -> None:
        r = self._session.put(
            self._url(f"/rest/v2/caches/{cache_name}/{key}"),
            data=json.dumps(value),
            headers={
                "Content-Type": "application/json",
                "Key-Content-Type": "application/x-java-object;type=java.lang.String",
            },
            verify=self._verify,
        )
        r.raise_for_status()

    def put_all(self, cache_name: str, entries: Dict[str, Any]) -> None:
        for key, value in entries.items():
            self.put(cache_name, key, value)

    def get(self, cache_name: str, key: str) -> Optional[Any]:
        r = self._session.get(
            self._url(f"/rest/v2/caches/{cache_name}/{key}"),
            headers={"Accept": "application/json"},
            verify=self._verify,
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def delete(self, cache_name: str, key: str) -> bool:
        r = self._session.delete(
            self._url(f"/rest/v2/caches/{cache_name}/{key}"),
            verify=self._verify,
        )
        return r.status_code == 204

    def query(
        self, cache_name: str, ickle_query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        body: Dict[str, Any] = {
            "query": ickle_query,
            "max_results": max_results,
        }
        r = self._session.post(
            self._url(f"/rest/v2/caches/{cache_name}?action=search"),
            json=body,
            headers={"Accept": "application/json"},
            verify=self._verify,
        )
        r.raise_for_status()
        result = r.json()
        return result.get("hits", [])

    def register_schema(self, schema_name: str, schema_content: str) -> None:
        # PUT is idempotent (create-or-replace); POST returns 409 if the schema
        # already exists, which would break re-use of a shared schema name
        # across multiple stores/caches of the same dimension.
        r = self._session.put(
            self._url(f"/rest/v2/schemas/{schema_name}"),
            data=schema_content,
            headers={"Content-Type": "text/plain"},
            verify=self._verify,
        )
        r.raise_for_status()
        # Infinispan returns HTTP 200 even when a schema fails to parse; the
        # parse error is reported in the response body instead. Surface it as
        # an error rather than silently registering an unusable schema.
        try:
            payload = r.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and payload.get("error"):
            error = payload["error"]
            cause = error.get("cause") or error.get("message") or str(error)
            raise ValueError(f"Failed to register schema {schema_name}: {cause}")
        logger.info("Registered schema %s", schema_name)

    def schema_exists(self, schema_name: str) -> bool:
        r = self._session.get(
            self._url(f"/rest/v2/schemas/{schema_name}"),
            verify=self._verify,
        )
        return r.status_code == 200

    def close(self) -> None:
        self._session.close()
