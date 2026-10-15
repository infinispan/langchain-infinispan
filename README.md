# LangChain Vector Store for Infinispan

[![CI](https://img.shields.io/github/actions/workflow/status/infinispan/langchain-infinispan/ci.yml?branch=main&style=for-the-badge&logo=github&label=CI)](https://github.com/infinispan/langchain-infinispan/actions/workflows/ci.yml)
[![PyPI Version](https://img.shields.io/pypi/v/langchain-infinispan?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/langchain-infinispan/)
![Python Versions](https://img.shields.io/badge/python-3.10--3.13-brightgreen.svg?style=for-the-badge&logo=python&logoColor=white)
[![License](https://img.shields.io/github/license/infinispan/spring-ai-infinispan?style=for-the-badge&logo=apache)](https://www.apache.org/licenses/LICENSE-2.0)
[![Project Chat](https://img.shields.io/badge/zulip-join_chat-pink.svg?style=for-the-badge&logo=zulip)](https://infinispan.zulipchat.com/)
[![GitHub Stars](https://img.shields.io/github/stars/infinispan/langchain-infinispan?style=for-the-badge&logo=github&color=DAA520)](https://github.com/infinispan/langchain-infinispan/stargazers)


langchain-infinispan is a [LangChain](https://www.langchain.com/) integration package that provides an
[Infinispan](https://infinispan.org/)-backed vector store for similarity search and document storage.

It connects to Infinispan via its REST API, supports multiple distance strategies (cosine, L2, inner product),
metadata filtering with the Ickle query language, and both Digest and Bearer token authentication.

## Getting Started

* [Package documentation](libs/infinispan/README.md)
* [Infinispan documentation](https://infinispan.org/)
* [LangChain documentation](https://docs.langchain.com/)

### Installation

```bash
pip install langchain-infinispan
```

### Quick Start

```python
from langchain_infinispan import InfinispanVectorStore
from langchain_openai import OpenAIEmbeddings

vector_store = InfinispanVectorStore(
    embedding=OpenAIEmbeddings(),
    cache_name="my_vectors",
    ispn_url="http://localhost:11222",
    ispn_user="admin",
    ispn_password="password",
)

# Add documents
vector_store.add_texts(
    ["Hello world", "Infinispan is fast"],
    metadatas=[{"source": "greeting"}, {"source": "fact"}],
)

# Similarity search
results = vector_store.similarity_search("hello", k=2)
```

### Requirements

- **Infinispan 15+** with vector search support
- **Python 3.10+**

## Contributing

For contributing guidelines please refer to this [document](CONTRIBUTING.md). All contributions are subject
to [Developer Certificate of Origin (DCO)](https://developercertificate.org/).

*The Infinispan project team*
