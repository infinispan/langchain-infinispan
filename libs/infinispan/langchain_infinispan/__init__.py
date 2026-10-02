from importlib.metadata import PackageNotFoundError, version

from langchain_infinispan._utilities import DistanceStrategy
from langchain_infinispan.client import InfinispanClient
from langchain_infinispan.vectorstores import InfinispanVectorStore

try:
    __version__ = version("langchain-infinispan")
except PackageNotFoundError:
    # Package is not installed (e.g. running from a source checkout).
    __version__ = "0.0.0"

__all__ = [
    "DistanceStrategy",
    "InfinispanClient",
    "InfinispanVectorStore",
    "__version__",
]
