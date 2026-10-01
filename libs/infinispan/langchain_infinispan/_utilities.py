from enum import Enum
from importlib.metadata import version


class DistanceStrategy(str, Enum):
    """Vector similarity functions supported by Infinispan.

    Each value is the exact token Infinispan accepts in the proto
    ``@Vector(similarity=...)`` annotation; it maps to a Lucene
    ``VectorSimilarityFunction`` on the server:

    - ``COSINE``            -> Lucene ``COSINE``
    - ``INNER_PRODUCT``     -> Lucene ``DOT_PRODUCT`` (expects unit-length vectors)
    - ``MAX_INNER_PRODUCT`` -> Lucene ``MAXIMUM_INNER_PRODUCT``
    - ``L2``                -> Lucene ``EUCLIDEAN`` (scored on squared L2 distance)
    """

    COSINE = "COSINE"
    INNER_PRODUCT = "INNER_PRODUCT"
    MAX_INNER_PRODUCT = "MAX_INNER_PRODUCT"
    L2 = "L2"


DEFAULT_CACHE_CONFIG_TEMPLATE = """<distributed-cache name="{cache_name}">
  <indexing storage="local-heap">
    <indexed-entities>
      <indexed-entity>{entity_type}</indexed-entity>
    </indexed-entities>
  </indexing>
</distributed-cache>"""


def _build_proto_schema(
    *,
    package_name: str,
    item_name: str,
    metadata_name: str,
    dimension: int,
    similarity: str,
) -> str:
    return f"""/**
 * @Indexed
 */
message {metadata_name} {{
   /** @Basic(projectable=true) */
   optional string name = 1;
   /** @Basic(projectable=true) */
   optional string value = 2;
   /** @Basic(projectable=true) */
   optional int64 value_int = 3;
   /** @Basic(projectable=true) */
   optional double value_float = 4;
}}

/**
 * @Indexed
 */
message {item_name} {{
   /** @Basic(projectable=true) */
   optional string id = 1;
   /** @Basic(projectable=true) */
   optional string text = 2;
   /** @Vector(dimension={dimension}, similarity={similarity}) */
   repeated float embedding = 3;
   /** @Embedded */
   repeated {metadata_name} metadata = 4;
}}
"""


def _proto_file_content(
    *,
    package_name: str,
    item_name: str,
    metadata_name: str,
    dimension: int,
    similarity: str,
) -> str:
    schema = _build_proto_schema(
        package_name=package_name,
        item_name=item_name,
        metadata_name=metadata_name,
        dimension=dimension,
        similarity=similarity,
    )
    return f'syntax = "proto2";\npackage {package_name};\n\n{schema}'


def user_agent() -> str:
    try:
        pkg_version = version("langchain-infinispan")
    except Exception:
        pkg_version = "unknown"
    return f"langchain-infinispan-py/{pkg_version}"
