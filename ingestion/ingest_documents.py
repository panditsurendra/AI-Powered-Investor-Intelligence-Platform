import os
import warnings
from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

from ingestion.pdf_to_markdown import PDFToMarkdownConverter
from ingestion.semantic_chunker import chunk_markdown

# --- FIXED: Importing the proper Native Qdrant structures ---
from ingestion.qdrant_uploader import QdrantStoreManager
from vectorstore.qdrant_store import QdrantRetriever
# ------------------------------------------------------------

from rag.kpi_extractor import extract_financial_metrics
from database.save_metrics import save_metrics

# Clean terminal warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
load_dotenv()


def parse_company_year(pdf_file: Path) -> tuple[str, str]:
    """Parse company and year from a PDF filename."""
    stem = pdf_file.stem
    parts = stem.split("_")

    if parts and parts[0].isdigit():
        year = parts[0]
        company = parts[-1]
    elif len(parts) >= 2:
        company = parts[0]
        year = parts[1]
    else:
        company = stem
        year = ""

    return company, year


def ingest_document(
    pdf_path: str,
    embeddings,
    vector_store
) -> None:
    """
    Ingest a single PDF document.
    """
    pdf_file = Path(pdf_path)

    company, year = parse_company_year(pdf_file)
    print(f"\n🚀 Ingesting {pdf_file.name} as company={company!r}, year={year!r}")

    # 1. Convert PDF to Markdown
    converter = PDFToMarkdownConverter()
    markdown_file = converter.convert_pdf(
        pdf_path=pdf_path,
        output_dir="data/markdown"
    )

    # 2. Semantic Chunking (using your local HF embeddings)
    chunks = chunk_markdown(
        markdown_file=markdown_file,
        embeddings=embeddings
    )
    print(f"📝 Generated {len(chunks)} semantic chunks for {pdf_file.name}")

    # 3. Upload chunks + metadata to local Qdrant
    vector_store.upload_chunks(
        chunks=chunks, 
        embeddings=embeddings,
        company=company,
        year=year,
        source_file=pdf_file.name
    )

    # 4. FIXED: Initialize the native retriever using the store and loaded embeddings
    native_retriever = QdrantRetriever(
        vector_store=vector_store.store, 
        embeddings=embeddings
    )

    metrics = extract_financial_metrics(
        retriever=native_retriever,
        company=company,
        year=int(year) if year.isdigit() else None
    )

    # 5. Persist metrics to PostgreSQL
    if metrics:
        save_metrics(
            company=company, 
            year=int(year) if str(year).isdigit() else None, 
            metrics=metrics
        )
        print(f"💾 Metrics saved to PostgreSQL database for {company} ({year})")


def ingest_directory(input_dir: str) -> None:
    """
    Ingest all PDFs from a directory.
    """
    # Initialize free local embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Initialize local free Qdrant connection
    vector_store = QdrantStoreManager(
        url="http://localhost:6335",
        collection_name="financial_documents",
    )

    pdf_files = list(Path(input_dir).glob("*.pdf"))
    print(f"🔍 Found {len(pdf_files)} PDF(s) in {input_dir}")

    for pdf_file in pdf_files:
        ingest_document(
            pdf_path=str(pdf_file),
            embeddings=embeddings,
            vector_store=vector_store
        )


if __name__ == "__main__":
    ingest_directory("data/raw_pdfs")












