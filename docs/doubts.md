1.) Tell me that is each chunk converted into seperate vector and that is stored quadrant seperately?

Yes, exactly! Each individual text chunk is converted into its own separate vector and stored as a distinct, separate "Point" in Qdrant.

If you look closely at how the data is uploaded (inside vectorstore/qdrant_store.py), the process works like this:

Iteration: The system loops through every single chunk one by one.
Vectorization: It passes the specific chunk of text to the embedding model (BAAI/bge-large-en), which converts that specific text into a 1024-dimensional math vector.
Point Creation: It creates a unique PointStruct for that vector. This point contains:
A unique ID.
The 1024-dimensional vector.
A Payload (which holds the original text of the chunk, plus metadata like the company name and year).
Storage: All of these individual points are then uploaded into the Qdrant database together.
So, if a 10-K report is broken down into 500 chunks, Qdrant will store 500 separate vectors.

This is crucial for the retrieval process in kpi_extractor.py. When you ask a question (like "What is the Net Income?"), the system converts your question into a vector and mathematically compares it against all those separate chunk vectors in Qdrant to find the 5 or 10 chunks that are most highly related to your specific question.


2.) how the kpis are extracted from the vectors, do we feed all vector to LLM to extract the KPI?
No, we do not feed all the vectors to the LLM. Doing so would crash the LLM because financial reports are massive and would easily exceed the LLM's maximum token limit (its "context window").

Furthermore, we never actually feed the mathematical vectors (the arrays of numbers) to the LLM. The vectors are purely used by Qdrant to find relevant information. The LLM only ever sees the original text (the payload) attached to those vectors.

Here is exactly how the KPIs are extracted in your code (specifically inside rag/kpi_extractor.py):

1. Filter by Metadata
First, the system doesn't search the entire database. It uses a Metadata Filter in Qdrant to pull only the chunks that match the specific company and year you are trying to analyze.

2. Rank the Chunks (The Keyword Heuristic)
Instead of feeding all the chunks of that report into the LLM, the retrieve_context() function in your code scores the text of each chunk based on how many financial keywords it contains. It looks for terms like: "net income", "operating income", "cash flow", "total assets", "revenue", etc.

The chunks are then sorted from highest score to lowest.

3. Build a Safe Context Window
The system takes the highest-scoring text chunks and starts concatenating them together into one large string. It stops adding chunks once it hits a hard character limit (in your code, 70,000 characters, which safely fits inside a ~20K token context window).

4. Feed the Text to the LLM
Finally, this highly dense, relevant block of text is injected into a strict prompt template that looks like this:

text
You are an expert financial analyst.
Company: Apple
Year: 2024
Context:
[... The 70,000 characters of highly relevant text chunks we just filtered ...]
Extract the following information:
1. Revenue
2. Net Income
...
5. Structured Extraction
This prompt is sent to the LLM (Qwen via HuggingFace). The LLM is forced by a Pydantic schema to return its answer as a perfectly formatted JSON object containing the exact numbers for the KPIs, which are then saved to the PostgreSQL database!

(Note: For the chat interface in chat.py, the flow is slightly different. It takes the user's specific question, turns the question into a vector, and asks Qdrant to find the 20 most mathematically similar text chunks to feed the LLM.)



