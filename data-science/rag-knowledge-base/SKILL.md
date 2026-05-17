---
name: rag-knowledge-base
description: "Use when: building or querying a RAG knowledge base, selecting embeddings, tuning retrieval, supplier memory systems, or 1688 sourcing intelligence. Covers ChromaDB, chunking, embedding models, and retrieval optimization."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [rag, knowledge-base, chromadb, embeddings, vector-search, supplier-memory, 1688]
    related_skills: [hermes-memory-hpc, n8n-hermes-integration, 1688-open-platform-api, llm-wiki, dspy]
---

# RAG Knowledge Base — Architecture & Implementation

## Overview

A RAG (Retrieval-Augmented Generation) knowledge base consists of:
- **Ingestion pipeline**: source documents → chunking → embedding → vector storage
- **Retrieval pipeline**: query → embedding → top-k similarity search → context assembly
- **Generation pipeline**: LLM reads context + query → augmented response

This skill covers the full stack: local ChromaDB deployment, document chunking strategies,
embedding model selection, retrieval optimization techniques, and a concrete 1688 supplier
knowledge base example built on top of `hermes-memory-hpc` and `1688-open-platform-api`.

---

## 1. ChromaDB Local Vector Database

### 1.1 Why ChromaDB

- Pure Python, no server dependency (embedded mode)
- Client–server mode via Docker for production
- LangChain / LlamaIndex first-class support
- Filterable metadata (`where` clause on any metadata field)
- Designed for collections: each collection = one embedding space

### 1.2 Docker Deployment (Recommended for Production)

```bash
mkdir -p ~/hermes-ai/chroma_data

cat > ~/hermes-ai/docker-compose.yml << 'EOF'
services:
  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - ./chroma_data:/chroma/data
    ports:
      - "8000:8000"
    restart: always
EOF

cd ~/hermes-ai && docker-compose up -d
```

- **Client URL**: `http://localhost:8000`
- **Docker internal**: `http://chromadb:8000`
- **Persistence**: Data survives container restarts via named volume mount

### 1.3 Python Client (embedded mode — no server needed)

```python
import chromadb
from chromadb.config import Settings

# Embedded mode (in-process, no server)
client = chromadb.Client()

# Or persistent mode (diYOUR_API_KEY, no server)
client = chromadb.PersistentClient(path="~/.hermes/chroma_data")

# Client-server mode (requires Docker)
client = chromadb.HttpClient(host="localhost", port=8000)

# Create a collection
collection = client.get_or_create_collection(
    name="suppliers",
    metadata={"description": "1688 supplier knowledge base"}
)

# Add documents
collection.add(
    documents=[
        "义乌星火包装 王老板 主营纸箱 报价5.2元 含税3天交货",
        "温州华鑫纸业 李总 主营瓦楞纸箱 报价4.9元 5天交货"
    ],
    metadatas=[
        {"supplier": "义乌星火包装", "product": "纸箱", "price": 5.2, "delivery_days": 3},
        {"supplier": "温州华鑫纸业", "product": "瓦楞纸箱", "price": 4.9, "delivery_days": 5}
    ],
    ids=["supplier_001", "supplier_002"]
)

# Query
results = collection.query(
    query_texts=["价格低、交货快的纸箱供应商"],
    n_results=3,
    where={"delivery_days": {"$lte": 5}}  # metadata filter
)
```

### 1.4 Collection Management

```python
# List all collections
print(client.list_collections())

# Get collection with embeddings
collection = client.get_collection("suppliers")

# Delete
client.delete_collection("stale_collection")

# Peek at first 10 items
print(collection.peek())

# Count
print(collection.count())
```

---

## 2. Document Chunking Strategies

Chunking directly controls retrieval precision and context quality.
Too large = noisy context. Too small = missing cross-chunk context.

### 2.1 Fixed-Size Chunking (Most Common)

```python
def chunk_text_fixed(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)
        start += chunk_size - overlap  # step = chunk_size - overlap
    return chunks
```

- **chunk_size=500**: Good for dense factual content (specs, prices)
- **chunk_size=1000**: Better for narrative or paragraphs
- **overlap=50–100**: Preserves cross-chunk context at section boundaries

### 2.2 Recursive Character Splitting (Recommended Default)

```python
def chunk_recursive(text: str, separators: list[str] = None) -> list[str]:
    """
    Split on hierarchical separators: paragraph → sentence → word.
    Respects semantic boundaries.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    chunks = []
    def split(text, sep_idx):
        if sep_idx >= len(separators):
            return [text] if text.strip() else []
        
        separator = separators[sep_idx]
        if not separator:
            return [text[i:i+1] for i in range(0, len(text), 1) if text[i:i+1].strip()]
        
        parts = text.split(separator)
        result = []
        for part in parts:
            if part.strip():
                if len(part) < 60:  # too short, try smaller separator
                    result.extend(split(part, sep_idx + 1))
                else:
                    result.append(part)
        return result
    
    return split(text, 0)

# LlamaIndex usage
from llama_index.node_parser import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", ", ", " "]
)
nodes = splitter.get_nodes_from_documents(documents)
```

### 2.3 Semantic Chunking (High Quality)

```python
def chunk_semantic(text: str, embedding_model, threshold: float = 0.7) -> list[str]:
    """
    Split at sentence boundaries where adjacent sentence similarity drops.
    Uses embedding cosine distance to detect topic shifts.
    """
    sentences = re.split(r'(?<=[。！？.!?])\s+', text)
    if len(sentences) <= 1:
        return [text]
    
    chunks = []
    current_chunk = [sentences[0]]
    
    for i in range(1, len(sentences)):
        # Compute similarity between current chunk end and next sentence
        prev_emb = embedding_model.encode(" ".join(current_chunk[-2:]))
        curr_emb = embedding_model.encode(sentences[i])
        sim = cosine_similarity(prev_emb, curr_emb)
        
        if sim < threshold:
            # Topic shift — start new chunk
            chunks.append("".join(current_chunk))
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])
    
    if current_chunk:
        chunks.append("".join(current_chunk))
    return chunks
```

### 2.4 Document-Aware Chunking (Hierarchical)

```python
def chunk_hierarchical(document: dict, chunk_size: int = 500) -> list[dict]:
    """
    Chunk structured documents (e.g. supplier profiles) preserving metadata.
    Each chunk inherits parent document metadata.
    """
    chunks = []
    text = document["content"]
    metadata = document.get("metadata", {})
    
    # Split by sections (assume ## heading format)
    sections = re.split(r'(?=^##\s+)', text, flags=re.MULTILINE)
    
    for section in sections:
        if not section.strip():
            continue
        # Further split oversized sections
        if len(section) > chunk_size:
            sub_chunks = chunk_text_fixed(section, chunk_size=chunk_size, overlap=50)
            for sc in sub_chunks:
                chunks.append({
                    "content": sc,
                    "metadata": {
                        **metadata,
                        "section": section.split("\n")[0][:100]  # heading
                    }
                })
        else:
            chunks.append({"content": section, "metadata": metadata})
    
    return chunks
```

### 2.5 Chunking Strategy Selection Guide

| Content Type | Recommended Strategy | chunk_size | overlap |
|---|---|---|---|
| Structured data (specs, prices) | Fixed-size | 300–500 | 50 |
| Long-form articles | Recursive character | 800–1000 | 100 |
| Supplier profiles / contracts | Semantic + hierarchy | 500–800 | 50 |
| QA pairs / FAQ | Sentence-level | 1 sentence | 0 |
| Code documentation | Recursive with `\n\n` first | 600 | 100 |

---

## 3. Embedding Model Selection

### 3.1 Local Embedding Models (Privacy-First, No API Cost)

```python
# Option A: sentence-transformers (CPU-friendly)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim, 22M params, ~120ms/batch on CPU
# Other good choices:
#   'all-mpnet-base-v2'   — higher quality, 768-dim, 110M params
#   'paraphrase-multilingual-MiniLM-L12-v2'  — multilingual (Chinese OK)

embeddings = model.encode(["供应商报价单", "price list"])

# Option B: Ollama (GPU-accelerated, OpenAI-compatible)
import openai
client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.embeddings.create(
    model="nomic-embed-text",  # 768-dim, ~137M params
    input="义乌星火包装纸箱供应商"
)
embedding = response.data[0].embedding
```

### 3.2 Cloud Embedding APIs

```python
# OpenAI
import openai
client = openai.OpenAI()
response = client.embeddings.create(
    model="text-embedding-3-small",  # 1536-dim, $0.02/1M tokens
    # text-embedding-3-large: 3072-dim, $0.13/1M tokens
    input="supplier price quote"
)

# Cohere
import cohere
co = cohere.Client("YOUR_API_KEY")
response = co.embed(
    texts=["supplier information"],
    model="embed-english-v3.0"  # or embed-multilingual-v3
)

# Jina AI (good for Chinese, free tier available)
import requests
resp = requests.post(
    "https://api.jina.ai/v1/embeddings",
    headers={"Authorization": "Bearer YOUR_JINA_TOKEN"},
    json={"model": "jina-embeddings-v3", "input": "中文供应商信息"}
)
```

### 3.3 Embedding Model Comparison

| Model | Dimensions | Context | Chinese | Speed | Quality | Cost |
|---|---|---|---|---|---|---|
| `all-MiniLM-L6-v2` | 384 | 256 tokens | ⚠️ Basic | Fast (CPU) | Good | Free |
| `all-mpnet-base-v2` | 768 | 384 tokens | ⚠️ Basic | Medium | Best (English) | Free |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 128 tokens | ✅ Good | Fast | Good | Free |
| `nomic-embed-text` (Ollama) | 768 | 2048 | ✅ Good | Fast (GPU) | Very Good | Free |
| `text-embedding-3-small` (OpenAI) | 1536 | 8191 | ✅ Good | Fast | Very Good | $0.02/1M |
| `text-embedding-3-large` (OpenAI) | 3072 | 8191 | ✅ Good | Fast | Excellent | $0.13/1M |
| `jina-embeddings-v3` (Jina) | 1024 | 8192 | ✅ Excellent | Fast | Excellent | Free tier |

### 3.4 Embedding Model Selection Decision Tree

```
Is the data purely English?
  → all-mpnet-base-v2 (best quality, free)

Is Chinese content involved?
  → nomic-embed-text (Ollama) OR jina-embeddings-v3 (Jina, free tier)

Is privacy critical (no data leaving machine)?
  → sentence-transformers local models (all-MiniLM-L6-v2)

Is quality more important than cost?
  → text-embedding-3-large (OpenAI) OR nomic-embed-text with larger model

Need GPU acceleration?
  → Ollama nomic-embed-text or text-embedding-3-* via API
```

### 3.5 Normalizing Embeddings

ChromaDB does **not** auto-normalize. For cosine similarity search:

```python
import numpy as np

def normalize(embedding: list[float]) -> list[float]:
    norm = np.linalg.norm(embedding)
    return [e / norm for e in embedding]

# Apply to all embeddings before storing
normalized_emb = normalize(embedding)
```

Alternatively, use ChromaDB's built-in `cosine` distance function (default) and
let the LLM handle normalization. ChromaDB normalizes automatically in cosine mode.

---

## 4. Knowledge Base Retrieval Optimization

### 4.1 Hybrid Search (Keyword + Vector)

```python
def hybrid_search(query: str, collection, embed_model, top_k: int = 5, alpha: float = 0.7):
    """
    Combines keyword BM25 scores with vector similarity.
    alpha=0.7 → 70% vector, 30% keyword
    """
    # Vector search
    query_emb = embed_model.encode(query)
    vec_results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k * 2
    )
    
    # Keyword search (simple TF-IDF — use rank_bm25 for production)
    from sklearn.feature_extraction.text import TfidfVectorizer
    docs = collection.get()["documents"]
    tfidf = TfidfVectorizer().fit_transform([query] + docs)
    keyword_scores = (tfidf[0] @ tfidf[1:].T).toarray()[0]
    
    # Merge scores
    doc_scores = {}
    for i, doc_id in enumerate(vec_results["ids"][0]):
        vec_score = 1 - vec_results["distances"][0][i]  # convert distance to similarity
        kw_score = keyword_scores[i] if i < len(keyword_scores) else 0
        doc_scores[doc_id] = alpha * vec_score + (1 - alpha) * kw_score
    
    ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return ranked
```

### 4.2 Metadata Filtering (Always Use First)

Filter **before** vector search, not after:

```python
# Good: filter first, then search within the filtered set
results = collection.query(
    query_embeddings=[query_emb],
    n_results=10,
    where={"product": "纸箱", "delivery_days": {"$lte": 5}}
)

# Bad: fetch all, then filter in Python
all_results = collection.get()
filtered = [r for r in all_results["documents"] if "纸箱" in r]  # expensive
```

### 4.3 Query Expansion (HyDE Pattern)

```python
def hyde_expand(query: str, llm_client) -> list[str]:
    """
    Use LLM to generate hypothetical document, then embed both.
    This expands the query with plausible answer content.
    """
    prompt = (
        f"Given the query: '{query}', write a hypothetical document "
        f"that would be a relevant answer. Be specific and include example details."
    )
    hypothetical = llm_client.chat.completions.create(
        model="qwen3-fast",
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content
    
    return [query, hypothetical]  # embed both, use better match

# Usage
query_embs = embed_model.encode(hyde_expand(user_query, llm_client))
results = collection.query(query_embeddings=[query_embs[0]], n_results=5)
```

### 4.4 Reranking with Cross-Encoders

```python
from sentence_transformers import CrossEncoder

# Cross-encoder is slower but more accurate than bi-encoder
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank(query: str, candidates: list[str], top_k: int = 3) -> list[tuple]:
    """Rerank candidates using cross-encoder scores."""
    pairs = [[query, doc] for doc in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
```

### 4.5 Context Compression / Summarization

```python
def contextual_compress(query: str, retrieved_docs: list[str], llm_client) -> str:
    """
    Use LLM to extract only the parts of each doc relevant to the query.
    Reduces context length while preserving relevance.
    """
    context = "\n\n".join(f"[Doc {i}]: {doc}" for i, doc in enumerate(retrieved_docs))
    prompt = (
        f"Given the query: '{query}', extract only the information "
        f"from each document that is relevant to the query. "
        f"Ignore irrelevant parts.\n\n{context}"
    )
    compressed = llm_client.chat.completions.create(
        model="qwen3-fast",
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content
    return compressed
```

### 4.6 Retrieval Evaluation

```python
def evaluate_retrieval(collection, embed_model, test_queries: list[dict]) -> dict:
    """
    Evaluate retrieval quality with precision@k and recall@k.
    test_queries = [{"query": "...", "relevant_ids": ["id1", "id2"]}]
    """
    from sklearn.metrics import precision_score, recall_score
    
    precisions, recalls = [], []
    for tq in test_queries:
        query_emb = embed_model.encode(tq["query"])
        results = collection.query(query_embeddings=[query_emb], n_results=5)
        retrieved = set(results["ids"][0])
        relevant = set(tq["relevant_ids"])
        
        tp = len(retrieved & relevant)
        precisions.append(tp / len(retrieved) if retrieved else 0)
        recalls.append(tp / len(relevant) if relevant else 0)
    
    return {
        "precision@5": np.mean(precisions),
        "recall@5": np.mean(recalls)
    }
```

---

## 5. 1688 Supplier Knowledge Base Example

### 5.1 Architecture Overview

```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  1688 Open API   │ ──▶ │  Ingestion      │ ──▶ │  ChromaDB        │
│  (商品/类目/SKU) │     │  (chunk+embed)  │     │  (suppliers col) │
└──────────────────┘     └─────────────────┘     └────────┬─────────┘
                                                          │
┌──────────────────┐     ┌─────────────────┐              │
│  User Query      │ ──▶ │  Hybrid Search  │ ◀───────────┘
│  ("找纸箱供应商") │     │  (vector+BM25)  │
└──────────────────┘     └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  LLM Synthesis │
                          │  (qwen3-fast)  │
                          └────────────────┘
```

### 5.2 Supplier Data Ingestion

```python
import chromadb
import re
import json
from datetime import datetime

# Initialize ChromaDB
client = chromadb.PersistentClient(path="~/.hermes/supplier_memory")
collection = client.get_or_create_collection(
    name="1688_suppliers",
    metadata={"description": "1688供应商知识库", "updated": str(datetime.now().date())}
)

def ingest_supplier(supplier_data: dict, embed_model):
    """
    Ingest a supplier profile into ChromaDB.
    supplier_data: {
        "supplier_name": "义乌星火包装",
        "contact": "王老板 138xxxx",
        "products": [{"name": "纸箱", "price": 5.2, "moq": 100}],
        "delivery_days": 3,
        "payment_terms": "月结30天",
        "rating": 4.8,
        "notes": "老板爽快，响应快"
    }
    """
    # Build a rich text representation for embedding
    products_text = " | ".join(
        f"{p['name']} 价格:{p['price']}元 MOQ:{p.get('moq', 1)}件"
        for p in supplier_data.get("products", [])
    )
    
    content = (
        f"供应商: {supplier_data['supplier_name']}\n"
        f"联系方式: {supplier_data.get('contact', '未知')}\n"
        f"主营产品: {products_text}\n"
        f"交货周期: {supplier_data.get('delivery_days', '未知')}天\n"
        f"付款方式: {supplier_data.get('payment_terms', '未知')}\n"
        f"店铺评分: {supplier_data.get('rating', '未知')}/5\n"
        f"备注: {supplier_data.get('notes', '无')}"
    )
    
    metadata = {
        "supplier_name": supplier_data["supplier_name"],
        "primary_product": supplier_data.get("products", [{}])[0].get("name", "未知"),
        "min_price": min(p.get("price", 999) for p in supplier_data.get("products", [{"price": 999}])),
        "max_price": max(p.get("price", 0) for p in supplier_data.get("products", [{"price": 0}])),
        "delivery_days": supplier_data.get("delivery_days", 0),
        "rating": supplier_data.get("rating", 0),
        "source": "1688_open_api"
    }
    
    doc_id = f"supplier_{supplier_data['supplier_name']}"
    collection.upsert(
        documents=[content],
        metadatas=[metadata],
        ids=[doc_id]
    )
    print(f"Ingested: {supplier_data['supplier_name']}")

# Example usage
supplier = {
    "supplier_name": "义乌星火包装",
    "contact": "王老板 13857654321",
    "products": [
        {"name": "纸箱 50*40*30", "price": 5.2, "moq": 100},
        {"name": "泡沫箱", "price": 8.5, "moq": 50}
    ],
    "delivery_days": 3,
    "payment_terms": "月结30天",
    "rating": 4.8,
    "notes": "老板爽快，响应快，适合急单"
}

# Note: embed_model from section 3
# ingest_supplier(supplier, embed_model)
```

### 5.3 Chunking Supplier Data

```python
def chunk_supplier_profile(supplier_data: dict) -> list[dict]:
    """
    Break a supplier profile into semantic chunks:
    - Contact chunk
    - Product chunks (one per product)
    - Business terms chunk
    """
    chunks = []
    supplier_id = f"supplier_{supplier_data['supplier_name']}"
    
    # Chunk 1: Contact + basic info
    chunks.append({
        "content": f"供应商: {supplier_data['supplier_name']} | "
                   f"联系方式: {supplier_data.get('contact', '未知')} | "
                   f"评分: {supplier_data.get('rating', '未知')}/5",
        "metadata": {"supplier": supplier_data["supplier_name"], "chunk_type": "contact"},
        "id": f"{supplier_id}_contact"
    })
    
    # Chunk 2: Per-product
    for i, product in enumerate(supplier_data.get("products", [])):
        chunks.append({
            "content": (
                f"产品: {product['name']} | "
                f"价格: {product.get('price', '询价')}元 | "
                f"MOQ: {product.get('moq', 1)}件 | "
                f"供应商: {supplier_data['supplier_name']}"
            ),
            "metadata": {
                "supplier": supplier_data["supplier_name"],
                "product": product.get("name", "未知"),
                "price": product.get("price", 0),
                "chunk_type": "product"
            },
            "id": f"{supplier_id}_product_{i}"
        })
    
    # Chunk 3: Business terms
    chunks.append({
        "content": (
            f"供应商: {supplier_data['supplier_name']} | "
            f"交货: {supplier_data.get('delivery_days', '未知')}天 | "
            f"付款: {supplier_data.get('payment_terms', '未知')} | "
            f"备注: {supplier_data.get('notes', '无')}"
        ),
        "metadata": {
            "supplier": supplier_data["supplier_name"],
            "chunk_type": "terms",
            "delivery_days": supplier_data.get("delivery_days", 0)
        },
        "id": f"{supplier_id}_terms"
    })
    
    return chunks

# Ingest all chunks
for chunk in chunk_supplier_profile(supplier):
    collection.upsert(
        documents=[chunk["content"]],
        metadatas=[chunk["metadata"]],
        ids=[chunk["id"]]
    )
```

### 5.4 Smart Supplier Query

```python
def query_suppliers(
    user_query: str,
    collection,
    embed_model,
    filters: dict = None,
    top_k: int = 5
) -> list[dict]:
    """
    Query the supplier knowledge base with natural language.
    Supports metadata filtering (price range, delivery time, product type).
    """
    # Embed query
    query_emb = embed_model.encode(user_query)
    
    # Build where clause from filters dict
    where_clause = {}
    if filters:
        if "min_price" in filters:
            where_clause["min_price"] = {"$gte": filters["min_price"]}
        if "max_price" in filters:
            where_clause.setdefault("min_price", {})["$lte"] = filters["max_price"]
        if "max_delivery_days" in filters:
            where_clause["delivery_days"] = {"$lte": filters["max_delivery_days"]}
        if "product" in filters:
            where_clause["primary_product"] = {"$eq": filters["product"]}
    
    # Retrieve
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        where=where_clause if where_clause else None,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format response
    formatted = []
    for i, doc_id in enumerate(results["ids"][0]):
        formatted.append({
            "supplier": results["metadatas"][0][i].get("supplier", "未知"),
            "product": results["metadatas"][0][i].get("primary_product", "未知"),
            "price": results["metadatas"][0][i].get("min_price", "询价"),
            "delivery_days": results["metadatas"][0][i].get("delivery_days", "未知"),
            "relevance_score": round(1 - results["distances"][0][i], 3),
            "chunk_type": results["metadatas"][0][i].get("chunk_type", "未知"),
            "content_snippet": results["documents"][0][i][:200]
        })
    
    return formatted

# Example queries
# find cheap fast suppliers
results = query_suppliers(
    "找价格便宜、交货快的纸箱供应商",
    collection,
    embed_model,
    filters={"max_delivery_days": 5, "product": "纸箱"}
)

# general search
results = query_suppliers(
    "义乌星火包装怎么样",
    collection,
    embed_model
)
```

### 5.5 1688 API → ChromaDB Pipeline

```python
import requests
import hmac
import hashlib
import base64
import time

APP_KEY = "YOUR_APP_KEY"
APP_SECRET = "YOUR_APP_SECRET"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

def sign_request(api_path, params):
    timestamp = str(int(time.time() * 1000))
    sorted_keys = sorted(params.keys())
    param_str = "&".join(f"{k}={params[k]}" for k in sorted_keys)
    string_to_sign = f"POST\ngw.open.1688.com\n{api_path}\n{param_str}"
    signature = base64.b64encode(
        hmac.new(app_secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    ).decode()
    return signature, timestamp

def get_category_suppliers(category_id: int, embed_model, max_results: int = 20):
    """Fetch suppliers for a 1688 category and ingest into ChromaDB."""
    api_path = f"/openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/{APP_KEY}"
    params = {
        "access_token": ACCESS_TOKEN,
        "categoryID": str(category_id),
        "webSite": "1688"
    }
    signature, timestamp = sign_request(api_path, params)
    params["_aop_signature"] = signature
    params["_aop_timestamp"] = timestamp
    
    # This API gets category attributes, not suppliers.
    # For actual supplier search, use 1688's product search API similarly.
    # The pattern is the same: sign → POST → parse → chunk → ingest.
    pass

def full_pipeline(embed_model):
    """
    Complete pipeline: 1688 API → clean → chunk → embed → ChromaDB.
    Run as a cronjob or on-demand refresh.
    """
    # Step 1: Fetch supplier data (via 1688 API or CDP browser automation)
    suppliers = fetch_suppliers_via_api()  # or via hermes-rpa CDP automation
    
    # Step 2: Chunk each supplier profile
    all_chunks = []
    for s in suppliers:
        all_chunks.extend(chunk_supplier_profile(s))
    
    # Step 3: Batch embed (faster than one-at-a-time)
    texts = [c["content"] for c in all_chunks]
    embeddings = embed_model.encode(texts, show_progress_bar=True)
    
    # Step 4: Batch ingest into ChromaDB
    collection.add(
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[c["metadata"] for c in all_chunks],
        ids=[c["id"] for c in all_chunks]
    )
    
    print(f"Ingested {len(all_chunks)} chunks from {len(suppliers)} suppliers")
```

### 5.6 Integration with hermes-memory-hpc

The ChromaDB supplier KB pairs with the L3 Obsidian layer for deep supplier history:

```python
# After a successful deal, update both ChromaDB and Obsidian
from memory_hpc import remember_supplier, save_to_obsidian

# L2: Update ChromaDB with new deal data
remember_supplier(
    supplier_name="义乌星火包装",
    product="纸箱 50*40*30",
    price=5.0,  # negotiated price
    delivery_days=3,
    attitude="积极",
    notes="成交价5.0元，老板爽快"
)

# L3: Archive full interaction to Obsidian
save_to_obsidian(
    vault_path="~/Obsidian/hermes-memory",
    record_type="supplier",
    data={
        "supplier": "义乌星火包装",
        "type": "成交记录",
        "date": str(datetime.now().date()),
        "deal_price": 5.0,
        "boss_reaction": "满意",
        "repeat_likelihood": "高"
    }
)
```

---

## Common Pitfalls

1. **Forgetting metadata filters**: Unfiltered vector search on large collections returns
   irrelevant results. Always apply `where` clause first.

2. **Mismatched chunk size with embedding context**: If your chunks are 1000 tokens but the
   embedding model only supports 256 tokens, context gets truncated. Verify model context length.

3. **Not normalizing embeddings for cosine similarity**: ChromaDB handles this by default
   when using `cosine` distance. But if you use raw dot-product, you must normalize.

4. **ChromaDB query() returns nested lists**: `results["documents"]` is `[["doc1", "doc2"]]`,
   not `["doc1", "doc2"]`. Access via `results["documents"][0][i]`. See `hermes-memory-hpc`
   SKILL.md for the full explanation and `memory_hpc.py` fix.

5. **Single-tenant ChromaDB in multi-user scenarios**: ChromaDB has no access control.
   For multi-user, deploy as a Docker service behind an auth layer, or use Qdrant / Milvus.

6. **Embedding model language mismatch**: `all-MiniLM-L6-v2` is English-first. For Chinese
   content, use `paraphrase-multilingual-MiniLM-L12-v2` or `nomic-embed-text`.

7. **Stale ChromaDB data**: ChromaDB doesn't auto-refresh. Set up a re-ingestion schedule
   (daily/weekly) for dynamic data like supplier prices.

8. **Using ChromaDB for production at scale (>100k docs)**: ChromaDB is great for
   prototyping and small-scale. For production with >100k documents, consider Qdrant
   (better filtering, HA) or Milvus (horizontal scaling).

---

## Verification Checklist

- [ ] ChromaDB Docker container starts and responds to health check
- [ ] Can create collection, add documents, and query with results returned
- [ ] Metadata filters correctly narrow results
- [ ] Chunk size appropriate for content type (test with 3+ different sizes)
- [ ] Embedding model produces fixed-dimension vectors (verify with `len(embeddings[0])`)
- [ ] Chinese queries return relevant results (if using multilingual content)
- [ ] Query latency < 200ms for collections up to 10k docs (local model)
- [ ] 1688 supplier data correctly chunks into contact/product/terms chunks
- [ ] Hybrid search improves over pure vector search on keyword-heavy queries
- [ ] ChromaDB data persists after container restart

---

## Related Skills

- `hermes-memory-hpc` — Supplier long-term memory (L2 ChromaDB + L3 Obsidian architecture)
- `n8n-hermes-integration` — n8n + ChromaDB Docker deployment
- `1688-open-platform-api` — 1688 API for supplier product/SKU data
- `llm-wiki` — Markdown knowledge base alternative (cross-reference RAG)
- `dspy` — DSPy declarative RAG pipeline optimization
