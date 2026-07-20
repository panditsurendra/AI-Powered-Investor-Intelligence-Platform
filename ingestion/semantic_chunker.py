from pathlib import Path

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker

from dotenv import load_dotenv
load_dotenv()



def read_markdown(markdown_file: str) -> str:
    """
    Read markdown content.

    Args:
        markdown_file: Markdown file path.

    Returns:
        Markdown content.
    """
    return Path(markdown_file).read_text(encoding="utf-8")


def chunk_markdown(
    markdown_file: str,
    embeddings
) -> list[Document]:
    """
    Generate semantic chunks from markdown.

    Args:
        markdown_file: Markdown file path.
        embeddings: Azure OpenAI embedding model.

    Returns:
        List of semantic chunks.
    """
    markdown_content = read_markdown(markdown_file)

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile"
    )

    return splitter.create_documents([markdown_content])



if __name__ == "__main__":
    import os
    from langchain_huggingface import HuggingFaceEmbeddings


    # endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    # api_key = os.getenv("AZURE_OPENAI_API_KEY")
    # api_version = os.getenv("AZURE_OPENAI_API_EMBEDDING_VERSION", "2023-05-15")
    # embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    # if not endpoint or not api_key:
    #     raise RuntimeError(
    #         "Missing Azure OpenAI credentials. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env."
    #     )

    print("Loading local Hugging Face Embedding Model (BAAI/bge-large-en)...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print("Embedding Model Loaded successfully.\n")

    script_dir = Path(__file__).parent

    markdown_file = (script_dir / "../data/markdown/2024_Apple.md").resolve()


    # Quick safety check to verify your file path
    if not os.path.exists(markdown_file):
        print(f"❌ Error: Could not find markdown file at: {markdown_file}")
    else:
        # 2. Process chunks locally
        chunks = chunk_markdown(
            markdown_file=markdown_file,
            embeddings=embeddings
        )

        print(f"Generated {len(chunks)} chunks\n")

        # 3. Print the first few chunks to inspect
        for index, chunk in enumerate(chunks[:3]):
            print("=" * 80)
            print(f"Chunk {index + 1}")
            print("=" * 80)
            print(chunk.page_content[:1000])
            print()