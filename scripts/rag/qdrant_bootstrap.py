#!/usr/bin/env python3
"""Bootstrap Qdrant collection for RAG."""
import os, sys
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLL = os.getenv("QDRANT_COLLECTION", "vtb_scrolls")
DIM = int(os.getenv("EMBED_DIM", "384"))

client = QdrantClient(url=QDRANT_URL)

if COLL in [c.name for c in client.get_collections().collections]:
    print(f"Collection {COLL} already exists")
    sys.exit(0)

client.recreate_collection(
    collection_name=COLL,
    vectors_config=qm.VectorParams(size=DIM, distance=qm.Distance.COSINE),
)
print(f"Created collection {COLL} dim={DIM}")
