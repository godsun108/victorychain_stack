# RAG & Qdrant Bootstrap

## Setup
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/rag/requirements_rag.txt
export QDRANT_URL=http://localhost:6333
export QDRANT_COLLECTION=vtb_scrolls
```

## Create Collection
```
python scripts/rag/qdrant_bootstrap.py
```

## Ingest Documents
Place source docs under `./data/scrolls` (supports .txt, .md, .markdown, .pdf).
```
python scripts/rag/rag_ingest.py --docs ./data/scrolls --chunk 800 --overlap 120
```

## Query Example (Python shell)
```python
from qdrant_client import QdrantClient
client = QdrantClient(url='http://localhost:6333')
res = client.search(collection_name='vtb_scrolls', query_vector=[0]*384, limit=3)
print(res)
```

Adjust embedding model or dimension as needed; default uses all-MiniLM-L6-v2 (384 dims, cosine).
