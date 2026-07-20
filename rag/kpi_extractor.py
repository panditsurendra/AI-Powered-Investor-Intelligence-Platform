import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# --- CHANGED: Swapped Azure for Local Qdrant & Ollama ---
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
# --------------------------------------------------------

load_dotenv()


class FinancialMetrics(BaseModel):
    revenue: str | int | None = Field(None, alias="Revenue")
    net_income: str | int | None = Field(None, alias="Net Income")
    operating_income: str | int | None = Field(None, alias="Operating Income")
    cash_flow: str | int | None = Field(None, alias="Cash Flow from Operating Activities")
    total_assets: str | int | None = Field(None, alias="Total Assets")
    total_liabilities: str | int | None = Field(None, alias="Total Liabilities")
    risk_factors: str | list | None = Field(None, alias="Top Risk Factors")
    growth_drivers: str | list | None = Field(None, alias="Top Growth Drivers")

    model_config = {"populate_by_name": True}


class Retriever:
    def __init__(self, client: QdrantClient):
        """
        Accepts a local QdrantClient and uses local HuggingFace embeddings for lookups.
        """
        self.client = client
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def invoke(
        self,
        query: str,
        company: str | None = None,
        year: int | None = None,
        top_k: int = 20
    ) -> list:
        """
        Retrieve relevant chunks from local Qdrant using native metadata filters.
        """
        must_conditions = []
        if company:
            must_conditions.append(
                qdrant_models.FieldCondition(
                    key="company",
                    match=qdrant_models.MatchValue(value=company)
                )
            )
        if year:
            must_conditions.append(
                qdrant_models.FieldCondition(
                    key="year",
                    match=qdrant_models.MatchValue(value=str(year))
                )
            )
            
        qdrant_filter = qdrant_models.Filter(must=must_conditions) if must_conditions else None

        query_vector = self.embeddings.embed_query(query)
        
        hits = self.client.query_points(
            collection_name="financial_documents",
            query=query_vector,
            query_filter=qdrant_filter,
            limit=top_k
        ).points
        
        from types import SimpleNamespace
        return [SimpleNamespace(page_content=hit.payload.get("content", "")) for hit in hits]


def retrieve_context(
    retriever: Retriever,
    company: str,
    year: int
) -> str:
    """
    Retrieve chunks using a keyword-based heuristic to find tabular financial data,
    ensuring we stay under the LLM's 32K token limit.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    # 1. Fetch all chunks for the company and year
    res = retriever.client.scroll(
        collection_name="financial_documents",
        scroll_filter=Filter(
            must=[
                FieldCondition(key="company", match=MatchValue(value=company)),
                FieldCondition(key="year", match=MatchValue(value=str(year)))
            ]
        ),
        limit=500
    )
    
    chunks = [hit.payload.get("content", "") for hit in res[0]]
    
    # 2. Score chunks based on exact financial keywords
    keywords = [
        "net income", "operating income", "cash flow", "total assets", 
        "total liabilities", "revenue", "gross margin", "risk factors"
    ]
    
    scored_chunks = []
    for chunk in chunks:
        lower_chunk = chunk.lower()
        score = sum(lower_chunk.count(kw) for kw in keywords)
        scored_chunks.append((score, chunk))
        
    # 3. Sort chunks by score descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # 4. Take the top chunks until we hit a safe character limit (e.g. 70,000 chars ~ 20K tokens)
    selected_content = []
    current_length = 0
    max_length = 70000
    
    for score, chunk in scored_chunks:
        if current_length + len(chunk) > max_length:
            continue
        if score > 0: # Only include chunks that have at least one keyword
            selected_content.append(chunk)
            current_length += len(chunk)
        
    return "\n\n".join(selected_content)


def build_extraction_prompt(
    company: str,
    year: int,
    context: str
) -> str:
    """
    Build KPI extraction prompt.
    """
    return f"""
You are an expert financial analyst.

Company: {company}
Year: {year}

Context:
{context}

Extract the following information:

1. Revenue
2. Net Income
3. Operating Income
4. Cash Flow from Operating Activities
5. Total Assets
6. Total Liabilities
7. Top Risk Factors
8. Top Growth Drivers

Instructions:

- Use only the provided context.
- Return null if unavailable.
- Financial values must match the report exactly.
- Risk factors should be concise.
- Growth drivers should be concise.
"""


def extract_financial_metrics(
    retriever: Retriever,
    company: str,
    year: int
) -> dict:
    """
    Extract KPIs using local RAG via Ollama structured outputs.
    """
    context = retrieve_context(
        retriever=retriever,
        company=company,
        year=year
    )

    prompt = build_extraction_prompt(
        company=company,
        year=year,
        context=context
    )

    # Initialize the free serverless cloud inference engine from HuggingFace
    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
    import os
    
    hf_llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-72B-Instruct",
        max_new_tokens=1024,
        temperature=0.01,
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
    )
    chat_model = ChatHuggingFace(llm=hf_llm)
    
    from langchain_core.output_parsers import JsonOutputParser
    
    parser = JsonOutputParser(pydantic_object=FinancialMetrics)
    prompt_with_instructions = prompt + "\n\n" + parser.get_format_instructions()
    
    response = chat_model.invoke(prompt_with_instructions)
    
    try:
        metrics = parser.parse(response.content)
    except Exception as e:
        print("Failed to parse JSON. Raw output:", response.content)
        metrics = {}
        
    return metrics


def main() -> None:
    company = "Apple"
    year = 2024

    # Connect to the local free Qdrant server instance
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    retriever = Retriever(client=client)

    results = extract_financial_metrics(
        retriever=retriever,
        company=company,
        year=year
    )

    print(f"\nExtracted KPIs for {company} {year}\n")

    for key, value in results.items():
        print(f"{key}:")
        print(value)
        print("-" * 80)

    from database.save_metrics import save_metrics
    save_metrics(
        company=company,
        year=year,
        metrics=results
    )


if __name__ == "__main__":
    main()