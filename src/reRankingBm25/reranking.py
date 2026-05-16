# =========================================================
# COMPLETE PRODUCTION-STYLE RAG PIPELINE
#
# Chunking
#   ↓
# Metadata
#   ↓
# Embeddings
#   ↓
# Qdrant Hybrid Search
#   ↓
# Reranking
#   ↓
# LLM Response
#
# =========================================================

# =========================================================
# INSTALL REQUIREMENTS
# =========================================================

# pip install \
# qdrant-client \
# sentence-transformers \
# rank-bm25 \
# langchain \
# langchain-community \
# langchain-openai \
# unstructured \
# pypdf


# =========================================================
# IMPORTS
# =========================================================

from qdrant_client import QdrantClient

from qdrant_client.models import (
    Distance,
    VectorParams
)

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder
)

from rank_bm25 import BM25Okapi

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_openai import ChatOpenAI

from langchain_core.messages import HumanMessage

import uuid

# =========================================================
# QDRANT CLIENT
# =========================================================

qdrant = QdrantClient(
    host="localhost",
    port=6333
)

COLLECTION_NAME = "production_rag"

# =========================================================
# EMBEDDING MODEL
# =========================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# =========================================================
# RERANKING MODEL
# =========================================================

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# =========================================================
# LOCAL LLM (LM STUDIO)
# =========================================================

llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
    model="local-model",
    temperature=0.3
)

# =========================================================
# SAMPLE DOCUMENT
# =========================================================

document = """

Kafka is a distributed event streaming platform.

LangGraph enables stateful AI workflows.

Qdrant is a vector database for semantic search.

Langfuse provides observability for AI systems.

RAG systems combine retrieval and generation.

Chunking strategies are important for retrieval quality.

"""

# =========================================================
# CHUNKING
# =========================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

chunks = splitter.split_text(document)

print("\n============================")
print(" CHUNKS ")
print("============================\n")

for i, chunk in enumerate(chunks):

    print(f"Chunk {i+1}:\n{chunk}\n")

# =========================================================
# CREATE COLLECTION
# =========================================================

existing = qdrant.get_collections().collections

collection_names = [
    c.name for c in existing
]

if COLLECTION_NAME not in collection_names:

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,

        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

# =========================================================
# EMBEDDINGS + METADATA
# =========================================================

points = []

for index, chunk in enumerate(chunks):

    embedding = embedding_model.encode(
        chunk
    ).tolist()

    metadata = {

        "text": chunk,

        "source": "sample_doc.txt",

        "chunk_id": index,

        "document_type": "technical",

        "author": "Manjeet"
    }

    points.append({

        "id": str(uuid.uuid4()),

        "vector": embedding,

        "payload": metadata
    })

# =========================================================
# INSERT INTO QDRANT
# =========================================================

qdrant.upsert(
    collection_name=COLLECTION_NAME,
    points=points
)

print("\nDocuments inserted into Qdrant\n")

# =========================================================
# USER QUERY
# =========================================================

query = input("\nEnter your query: ")

# =========================================================
# QUERY EMBEDDING
# =========================================================

query_vector = embedding_model.encode(
    query
).tolist()

# =========================================================
# VECTOR SEARCH
# =========================================================

vector_results = qdrant.query_points(

    collection_name=COLLECTION_NAME,

    query=query_vector,

    limit=5
).points

# =========================================================
# EXTRACT DOCS
# =========================================================

retrieved_docs = []

print("\n============================")
print(" VECTOR SEARCH RESULTS ")
print("============================\n")

for result in vector_results:

    text = result.payload["text"]

    score = round(result.score, 3)

    print(f"Score: {score}")

    print(f"Document:\n{text}\n")

    retrieved_docs.append(text)

# =========================================================
# HYBRID SEARCH (BM25)
# =========================================================

tokenized_docs = [
    doc.split()
    for doc in retrieved_docs
]

bm25 = BM25Okapi(tokenized_docs)

bm25_scores = bm25.get_scores(
    query.split()
)

print("\n============================")
print(" BM25 SCORES ")
print("============================\n")

for doc, score in zip(retrieved_docs, bm25_scores):

    print(f"Score: {score:.2f}")

    print(doc)

    print()

# =========================================================
# RERANKING
# =========================================================

pairs = [

    [query, doc]

    for doc in retrieved_docs
]

rerank_scores = reranker.predict(pairs)

reranked = list(
    zip(retrieved_docs, rerank_scores)
)

reranked.sort(
    key=lambda x: x[1],
    reverse=True
)

print("\n============================")
print(" RERANKED RESULTS ")
print("============================\n")

top_docs = []

for doc, score in reranked[:3]:

    print(f"Rerank Score: {score:.3f}")

    print(doc)

    print()

    top_docs.append(doc)

# =========================================================
# FINAL CONTEXT
# =========================================================

context = "\n".join(top_docs)

# =========================================================
# FINAL PROMPT
# =========================================================

prompt = f"""

Answer professionally using the context.

QUESTION:
{query}

CONTEXT:
{context}

"""

# =========================================================
# LLM RESPONSE
# =========================================================

response = llm.invoke(

    [
        HumanMessage(content=prompt)
    ]
)

# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n============================")
print(" FINAL RESPONSE ")
print("============================\n")

print(response.content)