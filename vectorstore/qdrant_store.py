import os
import uuid
from types import SimpleNamespace
from dotenv import load_dotenv

# Clean native Qdrant imports
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

load_dotenv()


class QdrantVectorStore:
    """Pure, native Qdrant vector store for managing financial document text chunks."""

    def __init__(self, collection_name: str, url: str | None = None) -> None:
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = collection_name
        self.client = QdrantClient(url=self.url)

    def upload_chunks(
        self,
        chunks,
        embeddings,
        company: str,
        year: str | int,
        source_file: str
    ) -> None:
        """
        Convert text chunks into vectors and upload them straight to Qdrant.
        """
        points = []

        for chunk in chunks:
            # Use the pipeline's embedding model to vectorize text chunks
            vector = embeddings.embed_query(chunk.page_content)

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "company": company,
                        "year": str(year),
                        "source_file": source_file,
                        "content": chunk.page_content
                    }
                )
            )

        # Direct, clean Qdrant storage command
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )

        print(f"✅ Successfully uploaded {len(points)} chunks to Qdrant collection: '{self.collection_name}'")


class QdrantRetriever:
    """
    Handles similarity lookup inside Qdrant with native metadata filtering constraints.
    """
    def __init__(self, vector_store: QdrantVectorStore, embeddings):
        self.client = vector_store.client
        self.collection_name = vector_store.collection_name
        self.embeddings = embeddings

    def invoke(
        self,
        query: str,
        company: str | None = None,
        year: int | str | None = None,
        top_k: int = 20
    ) -> list:
        """
        Look up relevant document fragments using standard Python variables.
        """
        # 1. Turn the user's natural language question into a vector
        query_vector = self.embeddings.embed_query(query)

        # 2. Build a clean, readable Qdrant filter constraint block
        must_conditions = []
        if company:
            must_conditions.append(
                FieldCondition(key="company", match=MatchValue(value=company))
            )
        if year:
            must_conditions.append(
                FieldCondition(key="year", match=MatchValue(value=str(year)))
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        # 3. Perform the mathematical nearest-neighbor search
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k
        ).points

        # 4. Pack things into a simple container so Ollama can read .page_content easily
        documents = []
        for hit in hits:
            content = hit.payload.get("content", "")
            documents.append(SimpleNamespace(page_content=content))
            
        return documents





