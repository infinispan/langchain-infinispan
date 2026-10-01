"""Integration tests for the supported vector similarity strategies.

Each ``DistanceStrategy`` value is written verbatim into the proto
``@Vector(similarity=...)`` annotation. Infinispan validates that token when a
schema is registered and rejects unknown values at parse time (reported in the
response body, which ``InfinispanClient.register_schema`` surfaces as a
``ValueError``). These tests register a schema for every strategy against a real
server so an invalid enum value fails loudly instead of only breaking the
non-default code paths.
"""

import uuid

import pytest

from langchain_infinispan import DistanceStrategy
from langchain_infinispan._utilities import _proto_file_content
from langchain_infinispan.client import InfinispanClient

from .conftest import ServerInfo


@pytest.mark.parametrize("strategy", list(DistanceStrategy), ids=lambda s: s.name)
def test_schema_registers_for_each_distance_strategy(
    strategy: DistanceStrategy, infinispan_server: ServerInfo
) -> None:
    """Every DistanceStrategy must emit a similarity token Infinispan accepts."""
    url, user, password = infinispan_server
    client = InfinispanClient(url=url, username=user, password=password, verify=False)

    # Unique package per run so parametrized cases never clash on type names.
    package = f"probe_{uuid.uuid4().hex[:8]}"
    proto = _proto_file_content(
        package_name=package,
        item_name=f"Item_{strategy.name}",
        metadata_name=f"Meta_{strategy.name}",
        dimension=3,
        similarity=strategy.value,
    )
    schema_name = f"{package}.{strategy.name}.proto"

    try:
        # Raises ValueError if Infinispan rejects the @Vector similarity token.
        client.register_schema(schema_name, proto)
    finally:
        client.close()
