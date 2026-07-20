import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from qdrant_client import QdrantClient
from rag.kpi_extractor import Retriever
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    company: str | None = None
    year: int | None = None

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Initialize local Qdrant client and retriever
        client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        retriever = Retriever(client=client)

        # Retrieve relevant context
        context = ""
        if request.company and request.year:
            docs = retriever.invoke(
                query=request.question,
                company=request.company,
                year=request.year
            )
        else:
            docs = retriever.invoke(
                query=request.question
            )
        context = "\n\n".join(doc.page_content for doc in docs)

        # Build chat prompt – include retrieved context and the user question
        prompt = f"You are an expert financial analyst. Use the following context from corporate reports to answer the user's question. If the context does not contain relevant information, politely indicate that you do not have enough data.\n\nContext:\n{context}\n\nUser Question: {request.question}\n\nAnswer:"

        hf_llm = HuggingFaceEndpoint(
            repo_id="Qwen/Qwen2.5-72B-Instruct",
            max_new_tokens=1024,
            temperature=0.01,
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
        )
        chat_model = ChatHuggingFace(llm=hf_llm)
        response = chat_model.invoke(prompt)
        
        answer = response.content
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))