from langchain_infinispan import __all__


def test_all_exports() -> None:
    expected = sorted(
        [
            "DistanceStrategy",
            "InfinispanClient",
            "InfinispanVectorStore",
        ]
    )
    assert sorted(__all__) == expected


def test_import_vector_store() -> None:
    from langchain_infinispan import InfinispanVectorStore  # noqa: F401


def test_import_client() -> None:
    from langchain_infinispan import InfinispanClient  # noqa: F401


def test_import_distance_strategy() -> None:
    from langchain_infinispan import DistanceStrategy  # noqa: F401
