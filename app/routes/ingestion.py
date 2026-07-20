import shutil
from fastapi import APIRouter, File, UploadFile
from pathlib import Path
import os
from langchain_huggingface import HuggingFaceEmbeddings
from ingestion.qdrant_uploader import QdrantStoreManager
from ingestion.ingest_documents import ingest_document

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    upload_dir = Path("data/raw_pdfs")
    upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = upload_dir / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

        # Initialize embeddings and vector store
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        vector_store = QdrantStoreManager(
            url="http://localhost:6335",
            collection_name="financial_documents",
        )

        ingest_document(
            pdf_path=str(file_path),
            embeddings=embeddings,
            vector_store=vector_store
        )

    return {
        "message": "Document uploaded successfully",
        "file_name": file.filename
    }