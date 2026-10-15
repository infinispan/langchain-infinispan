# Project Context: langchain-infinispan

langchain-infinispan is a LangChain integration package that provides an Infinispan-backed vector store for similarity search and document storage via Infinispan's REST API. It is written in Python.

## Shared guidelines
- Use the project's established patterns and terminology. When in doubt, follow the conventions already present in the codebase.
- Prefer clarity over cleverness. This is an open-source project with community contributors.
- Be aware of backward compatibility — the package is published on PyPI and users depend on the public API (`InfinispanVectorStore`, `InfinispanClient`, `DistanceStrategy`).

## Coding instructions
When planning and writing code, read and follow the instructions in AI-CODE.md.

## Testing instructions
When writing or modifying tests, read and follow the instructions in AI-TEST.md.

## Configuration change instructions
When adding or modifying vector store or client configuration, read and follow the instructions in AI-CONFIG.md.

## Documentation instructions
When writing or editing documentation, follow the conventions in the `documentation/` directory. AsciiDoc is the primary format for user-facing docs.

## Issue creation instructions
When creating GitHub issues, read and follow the instructions in AI-ISSUES.md.

## Maintaining AI context files
When making changes that alter the project structure, module organization, build process, or architectural patterns, check whether the relevant AI context files need updating: AGENTS.md, AI-CODE.md, AI-TEST.md, AI-CONFIG.md, and AI-ISSUES.md. Examples of changes that warrant updates: renaming or moving modules, adding new exports, changing build commands, introducing new frameworks or test patterns, or updating development conventions.
