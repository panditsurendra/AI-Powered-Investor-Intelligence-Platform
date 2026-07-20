[← Back to Main Menu](../README.md)
# AI Financial KPI Extractor Project

## The Goal
We built a system that takes a company's financial report (like Apple's 2024 Annual Report), reads through it using Artificial Intelligence (LLM), extracts key numbers (like Revenue and Net Income), and saves them into a PostgreSQL database. 

During the development, we faced **four major problems**. Here is a simple breakdown of what went wrong and how we fixed it. This is great for explaining the project in an interview!

---

### Problem 1: The AI was returning completely empty results
**What happened:** 
When we asked the AI to extract data, it couldn't find anything. 

**Why it happened:** 
We use a Vector Database (Qdrant) to search through the financial document. The tool we used to connect to the database (LangChain) was automatically looking for data using a nested folder structure like `metadata.company`. However, when we originally saved the document chunks into the database, we stored the tags simply as `company`. Because the tags didn't perfectly match, the database returned zero results to the AI.

**How we fixed it:** 
We stopped using the LangChain wrapper. Instead, we wrote custom code using Qdrant's native search functions (`query_points`). This allowed us to tell the database exactly where to look for the `company` and `year` tags, and the documents successfully started flowing to the AI!

---

### Problem 2: The AI output crashed the Python script
**What happened:** 
We got strange errors like `AttributeError: 'list' object has no attribute 'model_dump'` and the AI was spitting out random text like `[1.1]` instead of a neatly formatted data object.

**Why it happened:** 
We were using a free, serverless Hugging Face AI model (Qwen2.5). LangChain has a feature called `.with_structured_output()` which tries to force the AI to return a perfect Python object (a Pydantic model). However, open-source serverless models often get confused by this strict wrapper and return a list or badly formatted text, causing the code to crash when it tries to parse it.

**How we fixed it:** 
We removed the strict wrapper and switched to a `JsonOutputParser`. This is a much safer approach: it simply takes our required data format (Revenue, Net Income, etc.) and pastes it as plain-English instructions at the bottom of the AI prompt. The AI reads the instructions and easily outputs clean, standard JSON text, which we then load into our script safely.

---

### Problem 3: The "Table Data" Blindspot in RAG (Missing Net Income)
**What happened:** 
The AI successfully found Revenue, Risk Factors, and Growth Drivers. But it kept returning `None` for Net Income, Operating Income, Total Assets, and Total Liabilities, even though we knew they were in the PDF!
```text
Revenue: 391,035
Net Income: None
Operating Income: None
```

**Why it happened:** 
This is a classic problem in **RAG** (Retrieval-Augmented Generation). Our search query was something like: *"Find the income statement, balance sheet, risk factors, and revenue."* 
Because vector databases search by "semantic meaning" (how similar the sentences are), it heavily favored big, wordy paragraphs describing risks and revenue. The actual financial tables containing the hard numbers didn't have enough "words" in them to score high, so they got pushed completely out of the Top 10 search results! The AI literally couldn't see them.

**How we fixed it:** 
We tried to fix it by sending *all 92 chunks* of the document to the AI at once, but that led us straight into Problem 4...

---

### Problem 4: The 400 Bad Request / Token Limit Crash
**What happened:** 
When we tried to solve the RAG tabular data blindspot by sending all 92 chunks of the document to the AI at once, the script crashed with this error:
```text
httpx.HTTPStatusError: Client error '400 Bad Request' for url 'https://router.huggingface.co/v1/chat/completions'
Bad request: {'message': '{"object":"error","message":"Requested input length 132490 exceeds maximum input length 32767"...'}
```

**Why it happened:** 
This looks like a network rate limit, but it's actually a **Context Window Limit** error! Every LLM has a maximum "brain size" (called the context window). The Qwen2.5 serverless endpoint we used on Hugging Face has a strict limit of 32,767 tokens. When we fetched all 92 chunks of Apple's financial report and glued them together, it generated over 132,490 tokens! We tried to stuff 132,000 tokens into a 32,000 token brain, and Hugging Face's server immediately rejected the request.

**How we fixed it:** 
We built a character-length safety switch into a **Custom Hybrid Keyword Scorer**. We bypassed semantic search entirely, downloaded all 92 chunks into Python, and built a custom keyword scanner. It counted exactly how many times each chunk mentioned "net income", "total assets", and "cash flow". It then ranked the chunks by their score and packed the best ones together, stopping once the total character count hit 70,000 (which is approximately 20,000 tokens).

This guaranteed that we only sent the most relevant financial tables to the AI, completely avoiding the 32k token limit crash while perfectly extracting the numbers!

---

### The Final Result
By solving all of these problems, our extraction pipeline produces a clean, perfectly formatted JSON object that is ready to be loaded into PostgreSQL or sent to a frontend application:

```json
{
  "Revenue": "391,035",
  "Net Income": "93,736",
  "Operating Income": "123,216",
  "Cash Flow from Operating Activities": "118,254",
  "Total Assets": "364,980",
  "Total Liabilities": "308,030",
  "Top Risk Factors": [
    "Macroeconomic conditions...", 
    "Fluctuations in exchange rates..."
  ],
  "Top Growth Drivers": [
    "Services net sales...", 
    "Higher iPhone revenue..."
  ]
}
```
