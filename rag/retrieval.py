import os
import sys
import warnings
from dotenv import load_dotenv

# Suppress deprecation warnings for clean CLI outputs
warnings.filterwarnings("ignore", category=DeprecationWarning)
load_dotenv()

# --- CHANGED: Swapped Azure imports for local Qdrant & HF Embeddings ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
# ----------------------------------------------------------------------

def search_vectorstore(query: str, top: int = 5):
    # Fallback to local defaults if your .env isn't fully updated yet
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6335")
    collection_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "report_db")

    if not qdrant_url or not collection_name:
        raise RuntimeError(
            "Missing Qdrant configuration. Set QDRANT_URL and AZURE_SEARCH_INDEX_NAME in your .env."
        )

    # 1. Initialize the local embedding model to vectorize the search query
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # 2. Connect to your active local Qdrant collection
    store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=collection_name,
        url=qdrant_url,
    )

    # 3. Execute similarity search (automatically embeds the text query string)
    results = store.similarity_search(query, k=top)

    print(f"Query: {query!r}")
    print(f"Top: {top}")
    print(f"Results: {len(results)}\n")

    for idx, result in enumerate(results, start=1):
        content = None
        
        # 4. Smart extraction: Check if it's a LangChain Document object first
        if hasattr(result, "page_content"):
            content = result.page_content
        else:
            # Fallback handling matching your original structural parsing setup
            try:
                content = result.get("content")
            except Exception:
                content = getattr(result, "content", None)

            if content is None:
                try:
                    content = result["content"]
                except Exception:
                    content = str(result)

        snippet = content.strip().replace("\n", " ") if isinstance(content, str) else "<no content>"
        if len(snippet) > 350:
            snippet = snippet[:350].rstrip() + "..."

        print(f"Result {idx}")
        print(f"  content snippet: {snippet}")
        
        # Cleanly print metadata fields injected during ingestion
        if hasattr(result, "metadata") and result.metadata:
            company = result.metadata.get("company", "N/A")
            year = result.metadata.get("year", "N/A")
            print(f"  metadata: company={company!r}, year={year!r}")
            
        print("  " + "-" * 60)

    if not results:
        print("No results returned. Verify your index contents or try a different query.")

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m rag.retrieval \"your query here\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    search_vectorstore(query)


if __name__ == "__main__":
    main()





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




# 2. from_existing_collection(...)
# store = QdrantVectorStore.from_existing_collection(
#     embedding=embeddings,
#     collection_name=collection_name,
#     url=qdrant_url,
# )
# What it does

# It simply connects to a collection that already exists.

# Existing Qdrant Collection
#           ▲
#           │
#           │ connect
#           │
#      Your Python App

# It does not upload your documents.

# It does not create embeddings for your documents.

