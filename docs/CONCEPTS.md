[← Back to Main Menu](../README.md)
# Qdrant payload
A Qdrant payload is the JSON-like metadata and content stored alongside a vector, used to retrieve the original text and filter search results.

In Azure, you explicitly turn on features using boolean checkboxes like filterable=True or searchable=True.

In Qdrant, there are no boolean checkboxes. Instead, Qdrant relies entirely on the field_schema type to decide how a field behaves. By choosing a specific schema type, you are implicitly turning those features on.

field_schema="keyword" (Acts like filterable=True)
When you set company to "keyword", Qdrant automatically treats it as an exact-match filter.


# Quick Reference: Okapi BM25 Search

## 📌 What is BM25?
**BM25** (Best Matching 25) is the gold-standard algorithm for **lexical (keyword) search**. It estimates the relevance of a document to a given search query by looking for exact word matches. It is the underlying engine powering tools like Elasticsearch, OpenSearch, Apache Lucene, and Azure AI Search.

---

## 🛠️ How it Works: The 3 Pillars

Unlike basic word counting, BM25 uses three smart metrics to determine matching scores:

1. **Term Frequency (TF) Saturation ($k_1$):** 
   * Counts how often a keyword appears in a document.
   * *The Twist:* It applies a diminishing return. Mentioning "revenue" 3 times is much better than 1 time, but mentioning it 30 times isn't 10 times better than 3. The score levels off.
2. **Inverse Document Frequency (IDF):** 
   * Measures how rare a word is across your *entire* database.
   * Common words like "the" or "and" get a score of near 0. Rare, high-value words like "EBITDA" or "guanciale" receive massive scoring weights.
3. **Document Length Normalization ($b$):** 
   * Short documents where a word appears are rewarded; long, rambling documents are penalized.
   * Prevents a 500-page document from winning a search match simply because it naturally contains more words.

---

## 🏎️ BM25 vs. Vector Search

| Feature | BM25 (Lexical Search) | Vector Search (Dense Retrieval) |
| :--- | :--- | :--- |
| **Search Mechanism** | Exact keyword/character matching | Contextual & conceptual meaning |
| **Best For** | Part numbers, error codes, specific terminology, URLs | Synonyms, intent, open-ended phrasing |
| **Blind Spot** | Misses synonyms ("buy" won't match "purchase") | Misses exact product IDs or rare serial strings |

---

## 🚀 The Production Choice: Hybrid Search
In production Retrieval-Augmented Generation (RAG) applications, the best practice is to combine both search types:

$$Score_{Hybrid} = \text{BM25 Search} + \text{Vector Search}$$

By merging these scores using an algorithm like **Reciprocal Rank Fusion (RRF)**, you ensure your LLM receives context that captures both highly specific exact keywords (like an exact financial ledger item name) and the general thematic meaning of the prompt.



BM25 (Keyword Search) matches What You Spelled: It is a statistical word-counter. It looks for exact character matches between your query and the document. It cares about word frequency and text length, but it is completely blind to meaning or synonyms.

Similarity Search (Vector Search) matches What You Meant: It converts text into mathematical coordinates (embeddings). It calculates the geometric distance between those points. It finds text that is close in conceptual meaning, even if the exact words are completely different.