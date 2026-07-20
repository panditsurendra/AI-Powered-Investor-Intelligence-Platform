# import os
# from qdrant_client import QdrantClient
# from langchain_qdrant import QdrantVectorStore


# class QdrantStoreManager:
#     def __init__(self, url: str, collection_name: str):
#         self.url = url
#         self.collection_name = collection_name
#         # Keep a client reference because your RAG metrics extractor looks for it
#         self.client = QdrantClient(url=url)

#     def upload_chunks(self, chunks, embeddings, company, year, source_file):
#         """
#         Injects metadata into the chunks and uploads them to the local Qdrant instance.
#         """
#         # 1. Enrich LangChain Document metadata before saving
#         for chunk in chunks:
#             chunk.metadata["company"] = company
#             chunk.metadata["year"] = year
#             chunk.metadata["source_file"] = source_file

#         # 2. Upload to Qdrant
#         QdrantVectorStore.from_documents(
#             documents=chunks,
#             embedding=embeddings,
#             url=self.url,
#             collection_name=self.collection_name
#         )
#         print(f"✅ Successfully uploaded {len(chunks)} chunks to Qdrant collection '{self.collection_name}'")

import os
from dotenv import load_dotenv
from vectorstore.qdrant_store import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()

class QdrantStoreManager:
    """
    Ingestion wrapper that routes document chunks directly into 
    the native, high-performance Qdrant storage layer.
    """
    def __init__(self, collection_name: str, url: str | None = None):
        # Tie directly into your central vectorstore configuration
        qdrant_url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.store = QdrantVectorStore(collection_name=collection_name, url=qdrant_url)
        
        # Keep this reference variable alive so your pipeline orchestration doesn't break
        self.client = self.store.client

    def upload_chunks(
        self, 
        chunks, 
        embeddings, 
        company: str, 
        year: str | int, 
        source_file: str
    ) -> None:
        """
        Forwards incoming text chunks directly to the flat-payload uploader engine.
        """
        self.store.upload_chunks(
            chunks=chunks,
            embeddings=embeddings,
            company=company,
            year=year,
            source_file=source_file
        )

class QdrantRetrieverAdapter:
    def __init__(self, client: QdrantClient):
        self.client = client
    
    # If your extract_financial_metrics function relies on a custom retriever wrapper,
    # this class ensures it doesn't break due to missing attributes.





# store = QdrantVectorStore.from_documents(
#     documents=texts,
#     embedding=embeddings,
#     collection_name=collection_name,
#     url=qdrant_url,
# )
    
    # What it does

#   texts
#   ↓
# Embedding model
#   ↓
# Create vectors
#   ↓
# Create/connect to collection
#   ↓
# Upload vectors + documents












# you need to put the chunks into the existing collection

# Your current code is:

# qdrant = QdrantVectorStore.from_documents(
#     documents=texts,
#     embedding=embeddings,
#     url=url,
#     collection_name=collection_name,
#     prefer_grpc=False,
# )

# This is the part that:

# texts
#   ↓
# HuggingFace embedding model
#   ↓
# 1024-dimensional vectors
#   ↓
# Qdrant collection: report_db

# So the complete process is:

# Step 1: Create the empty collection

# Your create_index():

# client.create_collection(...)

# Result:

# Qdrant
# └── report_db
#     └── Empty
# Step 2: Add documents and embeddings

# Your ingestion code:

# QdrantVectorStore.from_documents(...)

# Result:

# Qdrant
# └── report_db
#     ├── Point 1
#     │   ├── Vector: 1024 numbers
#     │   └── Payload: text + metadata
#     │
#     ├── Point 2
#     │   ├── Vector: 1024 numbers
#     │   └── Payload: text + metadata
#     │
#     └── Point 3
#         ├── Vector: 1024 numbers
#         └── Payload: text + metadata