import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

def create_index(
    url: str,
    index_name: str,
    embedding_dimensions: int = 1024  # Core change: 1024 to match BAAI/bge-large-en
) -> None:
    """
    Create a local Qdrant collection mapping to the original Azure index design.
    """
    client = QdrantClient(url=url)

    # Wipe the old collection if it exists to ensure a clean schema reset
    if client.collection_exists(index_name):
        print(f"Collection '{index_name}' already exists. Recreating to apply fresh schema...")
        client.delete_collection(index_name)

    print(f"Creating local Qdrant collection '{index_name}' with {embedding_dimensions} dimensions...")
    
    # Configure the HNSW space matching your vector profile configuration
    client.create_collection(
        collection_name=index_name,
        vectors_config=VectorParams(
            size=embedding_dimensions,
            distance=Distance.COSINE  # Cosine similarity is highly optimal for BGE models
        )
    )

    # Replicate filterable=True and searchable=True using Qdrant Payload Indexes
    print("Applying payload indexes for metadata tracking...")

    # payload means the additional data stored along with a vector.
# Point
# ├── id
# ├── vector
# └── payload
    
    # Exact match filters (filterable fields)
    client.create_payload_index(collection_name=index_name, field_name="company", field_schema="keyword")
    client.create_payload_index(collection_name=index_name, field_name="year", field_schema="keyword")
    client.create_payload_index(collection_name=index_name, field_name="source_file", field_schema="keyword")
    
    # Full-text content search index (searchable field)
    client.create_payload_index(collection_name=index_name, field_name="content", field_schema="text")

    print(f"🚀 Success: Local collection '{index_name}' is fully initialized!")


if __name__ == "__main__":
    # Fallback to local defaults if environment variables aren't set yet
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "financial_documents")

    create_index(
        url=QDRANT_URL,
        index_name=INDEX_NAME
    )









# Unlike Azure, which requires you to strictly define every single column/field schema upfront, Qdrant is 
# a document-payload store. You only need to explicitly define your vector features (size and distance 
# metric). Other fields like company, year, and content are stored inside a flexible object called a Payload. 
# To make them filterable=True or searchable=True like they were in Azure, you create Payload Indexes.


# ⚠️ Crucial Warning: Vector Dimensions
# Your Azure script defaults to 1536 dimensions (the standard for paid OpenAI models). 
# Because you shifted your pipeline to use the local open-source model BAAI/bge-large-en, 
# you must change the dimensions to 1024. If you don't change this, Qdrant will throw a structural 
# error when your pipeline tries to upload the data.



# The create_index() function is just the setup/schema step. It does not upload your documents.

#     create the Qdrant collection

#     Approach 1: Let LangChain create the collection automatically

#     qdrant = QdrantVectorStore.from_documents(
#     documents=texts,
#     embedding=embeddings,
#     url=url,
#     collection_name=collection_name,
#     prefer_grpc=False,
#     )
    
#     can automatically create the collection if it does not already exist.


# Approach 2: Create the collection manually first

# Your  create_index() code does this:

# client.create_collection(
#     collection_name="report_db",
#     vectors_config=VectorParams(
#         size=1024,
#         distance=Distance.COSINE
#     )
# )

# qdrant = QdrantVectorStore.from_documents(
#     documents=texts,
#     embedding=embeddings,
#     url="http://localhost:6333",
#     collection_name="report_db",
# )

# In this approach, you should not use from_documents() to create the collection again. 
# Instead, connect to the existing collection and add documents.










# Why do you need payloads?
# 
# 
# question
#    ↓
# Embedding
#    ↓
# Vector similarity search
#    ↓
# Relevant Qdrant points

# Qdrant returns:

# Vector
#    +
# Payload

# The vector helps find the relevant chunk.

# The payload gives your application the actual text: