# Code-Aware RAG Pipeline

## Retrieval Architecture

```
Query
  │
  ▼
Query Preprocessing (Intent Classification + Keyword & Symbol Extraction)
  │
  ├──► Vector Search (pgvector cosine similarity on chunk embeddings)
  └──► Keyword Search (PostgreSQL full-text search on symbol names & comments)
  │
  ▼
Hybrid Fusion (Reciprocal Rank Fusion - RRF)
  │
  ▼
Symbol & Import Graph Expansion (Follow imports and callers to include related files)
  │
  ▼
Metadata Filtering (Language, file extension, commit/branch scope)
  │
  ▼
Context Window Budgeting & Compression
  │
  ▼
LLM Generation with Exact File/Line Citations
```

## Key Trade-offs & Decisions

| Decision | Option Selected | Rationale |
|---|---|---|
| **Chunking Strategy** | Code-Aware AST / Regex Chunking | Standard token splitting breaks functions across chunks. AST chunking preserves complete functions/classes with context. |
| **Vector Database** | PostgreSQL + `pgvector` | Avoids operational overhead of maintaining a separate vector DB while allowing join queries across metadata, symbols, and chunks in a single transaction. |
| **Hybrid Search** | Vector + Keyword + Graph Expansion | Vector search alone misses exact variable names (`createOrder`), keyword search misses semantic queries (`where is payment processed`). RRF combines both cleanly. |
