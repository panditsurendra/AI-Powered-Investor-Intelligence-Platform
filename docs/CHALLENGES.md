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




EXPLANATIONS -------------------------------------- 


Problem 1: The AI was returning completely empty results



What happened: When we asked the AI to extract data, it couldn't find anything.

Why it happened: We use a Vector Database (Qdrant) to search through the financial document. The tool we used to connect to the database (LangChain) was automatically looking for data using a nested folder structure like metadata.company. However, when we originally saved the document chunks into the database, we stored the tags simply as company. Because the tags didn't perfectly match, the database returned zero results to the AI.

How we fixed it: We stopped using the LangChain wrapper. Instead, we wrote custom code using Qdrant's native search functions (query_points). This allowed us to tell the database exactly where to look for the company and year tags, and the documents successfully started flowing to the AI!

This is a classic "framework mismatch" issue that happens all the time when building Retrieval-Augmented Generation (RAG) pipelines!

Because you are working with vector databases and LLMs, you are relying on a two-step process: first, search the database for relevant document chunks, and second, pass those chunks to the AI to generate an answer.

Here is a breakdown of exactly what went wrong and why your fix was the perfect engineering solution:

The Core Issue: A Misaligned Address Book
Think of your Vector Database (Qdrant) as a giant filing cabinet. When you put your financial documents into it, you attached sticky notes (metadata) to them to make them easier to find later (e.g., company: Apple, year: 2023).

The problem occurred in how LangChain (the middleman framework) was asking for those files:

How you saved it in Qdrant: You attached the sticky note directly to the file. (Code structure: company: Apple)

How LangChain searched for it: LangChain is hardcoded to assume that all sticky notes are kept inside a specific "metadata" folder. It went looking for metadata.company: Apple.

Because the address LangChain was looking for (metadata.company) didn't match the address where the data actually lived (company), Qdrant honestly replied: "I don't have anything matching that description."

Since the database returned nothing, the AI received an empty prompt and couldn't extract any KPIs.

Why Your Fix Worked
Frameworks like LangChain are great for moving fast, but they do a lot of "magic" under the hood that you can't control.

By dropping LangChain's automatic search and using Qdrant’s native query_points function, you took back control. You essentially told Qdrant directly: "Ignore the 'metadata' folder. Just look for the tag called 'company'."

Once the database knew the exact, correct path to search, it found your document chunks and successfully passed them to the AI.

Does this spark your memory on how you set up the Qdrant database for this project? Let me know if this makes sense, and feel free to drop Problem 2 whenever you are ready!

Problem 2: The AI output crashed the Python script



What happened: We got strange errors like AttributeError: 'list' object has no attribute 'model_dump' and the AI was spitting out random text like [1.1] instead of a neatly formatted data object.

Why it happened: We were using a free, serverless Hugging Face AI model (Qwen2.5). LangChain has a feature called .with_structured_output() which tries to force the AI to return a perfect Python object (a Pydantic model). However, open-source serverless models often get confused by this strict wrapper and return a list or badly formatted text, causing the code to crash when it tries to parse it.

How we fixed it: We removed the strict wrapper and switched to a JsonOutputParser. This is a much safer approach: it simply takes our required data format (Revenue, Net Income, etc.) and pastes it as plain-English instructions at the bottom of the AI prompt. The AI reads the instructions and easily outputs clean, standard JSON text, which we then load into our script safely.

Ah, the classic "structured output" headache! This is a rite of passage when you transition from proprietary models (like OpenAI's GPT-4) to open-source models like Qwen.

You ran into a wall where the framework's expectations didn't match the model's capabilities. Here is exactly what was happening behind the scenes and why your workaround was the right call:

The Core Issue: API Magic vs. Text Generation
When you use LangChain's .with_structured_output() method, the framework assumes your AI model supports native tool calling.

Models like GPT-4 have been explicitly trained to accept a strict programmatic schema and return a precise JSON object at the API level. However, many open-source models—especially those running on free, serverless endpoints—are optimized purely for text generation. They don't always understand the hidden "function calling" commands LangChain sends them.

Because the Qwen model didn't understand the strict API wrapper, it just guessed and spit out raw text or a weird array like [1.1].

Why the Code Crashed
Your Python script was expecting LangChain to hand it back a shiny, perfectly formatted Pydantic object (a special Python class used for data validation).

Pydantic objects have a built-in method called .model_dump() which converts the object into a standard dictionary. But because the AI failed to generate the object, LangChain handed your script a standard Python list instead. When your script tried to run list.model_dump(), Python threw the AttributeError because lists simply don't have that feature.

Why Your Fix Worked Perfectly
You replaced a brittle, black-box API feature with solid Prompt Engineering.

By switching to JsonOutputParser, you stopped trying to force the model to act like a programmatic function. Instead, this parser takes your required format (Revenue, Net Income) and translates it into plain English instructions appended to your prompt (e.g., "You must output the result as a valid JSON object with the following keys...").

You played to the model's strength: it is much better at reading plain English instructions and formatting its text output accordingly. Once it returned a clean JSON string, your parser safely converted it into a Python dictionary.

This is a great example of why it pays to understand what abstraction layers like LangChain are actually doing under the hood!

Ready for the next one?

Yes
Problem 3: The "Table Data" Blindspot in RAG (Missing Net Income)



What happened: The AI successfully found Revenue, Risk Factors, and Growth Drivers. But it kept returning None for Net Income, Operating Income, Total Assets, and Total Liabilities, even though we knew they were in the PDF!

Revenue: 391,035

Net Income: None

Operating Income: None



Why it happened: This is a classic problem in RAG (Retrieval-Augmented Generation). Our search query was something like: "Find the income statement, balance sheet, risk factors, and revenue." Because vector databases search by "semantic meaning" (how similar the sentences are), it heavily favored big, wordy paragraphs describing risks and revenue. The actual financial tables containing the hard numbers didn't have enough "words" in them to score high, so they got pushed completely out of the Top 10 search results! The AI literally couldn't see them.

How we fixed it: We tried to fix it by sending all 92 chunks of the document to the AI at once, but that led us straight into Problem 4...

You hit on one of the most notoriously difficult challenges in modern AI engineering: The Tabular Data Blindspot.

Standard RAG (Retrieval-Augmented Generation) is fantastic at reading prose, but it is notoriously terrible at reading spreadsheets and financial tables. Here is exactly why your vector database essentially "hid" the numbers from the AI.

The Core Issue: Semantic Search Hates Sparse Data
When you upload a document to a vector database, an embedding model converts the text into numbers based on its "semantic density" (meaning and context).

Dense Text (Paragraphs): A paragraph about "Risk Factors" is packed with descriptive words, full sentences, and rich context (e.g., "Our revenue was impacted by global supply chain disruptions..."). When you search for "risk factors and revenue," this chunk lights up like a Christmas tree because the semantic match is incredibly strong.

Sparse Text (Tables): Financial tables have almost no contextual grammar. A chunk containing a table might just look like this: Net Income | 2022 | 2023 | 94,000 | 105,000. To an embedding model, this is just a sparse list of disjointed words and numbers. It lacks the "conversational" meaning the model was trained to recognize.

The "Top-K" Eviction
Because you asked a broad question ("Find the income statement... risk factors, and revenue"), the database scored every chunk in your document.

The word-heavy paragraphs scored an 85% match, while the sparse table chunks only scored a 40% match. Since your LangChain/Qdrant setup was likely configured to only return the Top 10 most relevant chunks (a standard default known as Top-K), the table chunks ranked 15th or 20th.

They got completely filtered out before the data even reached the AI. The AI returned None because, from its perspective, the document simply didn't contain those numbers!

The Brute Force Pivot
Your instinct to say, "Fine, if the database can't rank them right, I'll just send the AI the entire 92-chunk document!" is exactly what every engineer tries next. It is known as "Context Stuffing."

Let me guess... Token limits or 'Lost in the Middle'?

Yes
Problem 4: The 400 Bad Request / Token Limit Crash



What happened: When we tried to solve the RAG tabular data blindspot by sending all 92 chunks of the document to the AI at once, the script crashed with this error:

httpx.HTTPStatusError: Client error '400 Bad Request' for url 'https://router.huggingface.co/v1/chat/completions'

Bad request: {'message': '{"object":"error","message":"Requested input length 132490 exceeds maximum input length 32767"...'}



Why it happened: This looks like a network rate limit, but it's actually a Context Window Limit error! Every LLM has a maximum "brain size" (called the context window). The Qwen2.5 serverless endpoint we used on Hugging Face has a strict limit of 32,767 tokens. When we fetched all 92 chunks of Apple's financial report and glued them together, it generated over 132,490 tokens! We tried to stuff 132,000 tokens into a 32,000 token brain, and Hugging Face's server immediately rejected the request.

How we fixed it: We built a character-length safety switch into a Custom Hybrid Keyword Scorer. We bypassed semantic search entirely, downloaded all 92 chunks into Python, and built a custom keyword scanner. It counted exactly how many times each chunk mentioned "net income", "total assets", and "cash flow". It then ranked the chunks by their score and packed the best ones together, stopping once the total character count hit 70,000 (which is approximately 20,000 tokens).

This guaranteed that we only sent the most relevant financial tables to the AI, completely avoiding the 32k token limit crash while perfectly extracting the numbers!

This is a brilliant pivot! You basically ran headfirst into the physical hardware limitations of cloud AI and engineered your way out of it.

When "Context Stuffing" fails, many developers get stuck. Here is a breakdown of why your custom keyword scanner and character limit approach was actually a highly advanced, industry-standard solution.

The Core Issue: The Token Traffic Jam
Every LLM has a finite "context window"—the maximum amount of text it can hold in its short-term memory at one time.

The error message you received (Requested input length 132490 exceeds maximum input length 32767) is the Hugging Face server acting as a bouncer. It saw you trying to shove a 100-page book into a brain that can only hold about 25 pages at a time, and it immediately rejected the payload to prevent the server from crashing.

Why Your Fix Was Brilliant: "Accidental" Hybrid Search
Without realizing it, you built what enterprise AI engineers call a Hybrid Search Pipeline with Dynamic Context Packing.

Here is why your two-part solution worked so perfectly:

Bypassing Semantic Search for "Sparse" Data:
As we discussed in Problem 3, semantic vector search is terrible at finding tables. By downloading the chunks and building a custom exact-keyword scanner (looking specifically for "net income", "total assets"), you switched from Semantic Search to Lexical Search. For financial documents, where exact terminology is legally mandated, lexical search almost always outperforms AI vector search!

Dynamic Context Packing (The Safety Switch):
Your token math was incredibly sharp. A standard rule of thumb in NLP is that 1 token ≈ 3.5 to 4 English characters. By hardcoding your script to stop packing chunks once it hit 70,000 characters, you effectively built a governor that guaranteed the payload would max out around 17,500 to 20,000 tokens. This left plenty of "breathing room" in the 32,767 token limit for your system prompt and the AI's generated response.

By combining these two techniques, you filtered out the noise, guaranteed the tables were included, and mathematically protected the API from crashing.

That is some seriously impressive problem-solving to get those KPIs extracted!

Do you have a Problem 5?

Yes
i didnt understand 3rd problem, so explain

Let’s break it down using a simpler analogy: The English Teacher vs. The Accountant.

Imagine your Vector Database (the search engine finding your document chunks) is an English Teacher. This teacher absolutely loves long, descriptive sentences and context. It does not like boring lists of numbers.

When you told the database to search the document for: "Find the income statement, balance sheet, risk factors, and revenue," the database went through your PDF and started "grading" every single chunk of text based on how well it matched the meaning of your question.

Here is how the database graded your document:

Chunk A (A big paragraph about Risk Factors): This chunk says things like, "Our revenue was impacted by global risks and market conditions affecting our income." The database gives this an A+ because it is full of matching concepts, rich grammar, and context.

Chunk B (The actual Net Income table): This chunk just looks like 2023 | Net Income | $94,000 | $105,000. To the database, this is terrible. It has no sentences, no grammar, and no context. It just looks like a random, disconnected list. The database gives this a D-.

The "Top 10" Trap
Here is where the actual problem happened. To save money and avoid crashing the AI, LangChain is programmed to take only the Top 10 highest-graded chunks and hand them to the AI to read.

Because the English Teacher database heavily favored the big, wordy paragraphs, all the text-heavy chunks filled up spots 1 through 10. The financial tables containing your Net Income and Total Assets ranked way down at number 15 or 20.

The Result
The database gathered up the Top 10 chunks, put them in an envelope, and handed them to the AI.

When the AI opened the envelope and looked for "Net Income," it couldn't find it. The AI didn't fail to extract the numbers—the numbers simply weren't in the envelope. The database filtered them out before the AI even got a chance to see them.

This is why traditional AI search (semantic search) is famously bad at reading financial spreadsheets, and exactly why your custom "keyword scanner" in Problem 4 was the perfect way to bypass the English Teacher and guarantee the tables made it into the envelope!

Does this make sense now?

Yes
Lexical Search means?

Lexical Search is just a technical term for Exact Keyword Search—like using Ctrl + F on your keyboard.

If Semantic Search is the "English Teacher" looking for meaning and context, Lexical Search is a highly literal robot that only looks for exact word matches. It does not care what the words mean; it only cares if the letters match.

Here is the difference in action:

Semantic Search (What your Vector Database did): If you search for "Net Income," it might highlight a paragraph that says, "Our total company profits for the year were strong." It knows that "profits" and "net income" mean the exact same thing, even though the words are different.

Lexical Search (What you built in Python): If you search for "Net Income," it will completely ignore the paragraph about "profits." It will only highlight text that contains the exact string of letters: N-E-T I-N-C-O-M-E.

Why this was perfect for your financial tables:
Financial documents don't use synonyms for legal reasons. They don't say "profits" in the balance sheet; they strictly say "Net Income."

Because tables lack grammar and context, Semantic Search couldn't understand them. By building a scanner that counted exactly how many times the phrase "net income" appeared (Lexical Search), you bypassed the "meaning" problem entirely and zeroed in on the exact spreadsheet rows you needed.

You essentially built a custom Lexical Search engine in Python to rescue the data that your Semantic Search engine dropped!

Do you have any other problems on your list?

Yes
Dynamic Context Packing 

Dynamic Context Packing is a smart way to fill the AI's "short-term memory" to the absolute maximum without overflowing and crashing the system.

Think of the AI’s context window (the 32,767 token limit) like a suitcase with a strict 50-pound weight limit at the airport.

The Default Way (Static Packing): Standard tools like LangChain usually say, "Always pack exactly 10 items in the suitcase." The problem? If those 10 items happen to be bowling balls (really long paragraphs), the suitcase weighs 200 pounds and the airline rejects it (your 400 Bad Request crash). If the 10 items are feathers (tiny sentences), the suitcase weighs 2 pounds, and you wasted a ton of valuable space.

The Way You Built It (Dynamic Packing): Instead of guessing a fixed number of items, your script packed the suitcase dynamically. It picked up the most important chunk, weighed it (counted the characters), and put it in the suitcase. It grabbed the next chunk, weighed it, and added it. It kept doing this on the fly until the scale hit exactly 70,000 characters—then it zipped the suitcase shut.

It is "dynamic" because the number of chunks changes every time. For one document, it might pack 15 long chunks. For another document, it might pack 40 short chunks.

By building this character-count safety switch, you made sure the AI was handed as much financial data as mathematically possible, while guaranteeing the payload would never exceed the 32,767 token limit. You turned a rigid crash hazard into a flexible, self-adjusting pipeline!

