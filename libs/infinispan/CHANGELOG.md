# Changelog

All notable changes to `langchain-infinispan` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-02

Initial release of the Infinispan integration for LangChain.

### Added

- `InfinispanVectorStore`, a LangChain `VectorStore` backed by Infinispan 15+
  vector search over the REST API.
- `InfinispanClient`, a thin REST wrapper handling schema registration, cache
  creation, writes, queries, and deletes.
- Configurable distance strategies (`COSINE`, `INNER_PRODUCT`,
  `MAX_INNER_PRODUCT`, `L2`) mapped to Infinispan's accepted `@Vector`
  similarity tokens.
- Normalized relevance scores in `[0, 1]` via
  `similarity_search_with_relevance_scores`, alongside native scores from
  `similarity_search_with_score` / `similarity_search_with_score_by_vector`.
- Metadata filtering with both dict filters and langchain-core
  `FilterDirective` expressions translated to Ickle queries.
- Type-aware metadata storage for `str`, `int`, and `float` values.
- Conformance with the LangChain standard `VectorStoreIntegrationTests` suite.

[Unreleased]: https://github.com/infinispan/langchain-infinispan/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/infinispan/langchain-infinispan/releases/tag/v0.1.0
