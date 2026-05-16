# =========================================================
# IMPORTS
# =========================================================

from neo4j import GraphDatabase

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_openai import ChatOpenAI

from langchain_core.messages import HumanMessage

import re

# =========================================================
# NEO4J CONNECTION
# =========================================================

URI = "bolt://localhost:7687"

USERNAME = "neo4j"

PASSWORD = "password"

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# =========================================================
# LOCAL LLM (LM STUDIO)
# =========================================================

llm = ChatOpenAI(

    base_url="http://localhost:1234/v1",

    api_key="lm-studio",

    model="local-model",

    temperature=0
)

# =========================================================
# SAMPLE DOCUMENT
# =========================================================

document = """

Kafka uses Zookeeper for cluster coordination.

LangGraph orchestrates AI agents.

Qdrant stores vector embeddings.

Langfuse provides observability for AI systems.

Kafka integrates with LangGraph for event-driven AI.

"""

# =========================================================
# CHUNKING
# =========================================================

splitter = RecursiveCharacterTextSplitter(

    chunk_size=200,

    chunk_overlap=50
)

chunks = splitter.split_text(document)

print("\n==============================")
print(" CHUNKS ")
print("==============================\n")

for chunk in chunks:

    print(chunk)

    print()

# =========================================================
# ENTITY + RELATION EXTRACTION
# =========================================================

def extract_graph(chunk):

    prompt = f"""

Extract entities and relationships.

Return ONLY in format:

ENTITY1 | RELATION | ENTITY2

Example:
Kafka | USES | Zookeeper

TEXT:
{chunk}

"""

    response = llm.invoke(
        [
            HumanMessage(content=prompt)
        ]
    )

    return response.content

# =========================================================
# STORE GRAPH IN NEO4J
# =========================================================

def store_graph(relation_text):

    lines = relation_text.split("\n")

    with driver.session() as session:

        for line in lines:

            # ============================================
            # Skip invalid lines
            # ============================================

            if "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]

            if len(parts) != 3:
                continue

            entity1, relation, entity2 = parts

            # ============================================
            # CLEAN RELATIONSHIP NAME
            # ============================================

            relation = (
                relation
                .strip()
                .upper()
                .replace(" ", "_")
                .replace("-", "_")
                .replace("/", "_")
            )

            # ============================================
            # CLEAN ENTITY NAMES
            # ============================================

            entity1 = entity1.strip()

            entity2 = entity2.strip()

            print(
                f"\nStoring: {entity1} -[{relation}]-> {entity2}"
            )

            # ============================================
            # CYPHER QUERY
            # ============================================

            query = f"""

            MERGE (a:Entity {{name: $entity1}})

            MERGE (b:Entity {{name: $entity2}})

            MERGE (a)-[:{relation}]->(b)

            """

            # ============================================
            # EXECUTE QUERY
            # ============================================

            session.run(

                query,

                entity1=entity1,

                entity2=entity2
            )

# =========================================================
# PROCESS CHUNKS
# =========================================================

for chunk in chunks:

    relations = extract_graph(chunk)

    print("\n==============================")
    print(" EXTRACTED RELATIONS ")
    print("==============================\n")

    print(relations)

    store_graph(relations)

# =========================================================
# GRAPH QUERY
# =========================================================

def query_graph(entity):

    with driver.session() as session:

        query = """

        MATCH (a)-[r]->(b)

        WHERE a.name = $entity

        RETURN a.name, type(r), b.name

        """

        result = session.run(
            query,
            entity=entity
        )

        print("\n==============================")
        print(" GRAPH RESULTS ")
        print("==============================\n")

        context = []

        for record in result:

            source = record["a.name"]

            relation = record["type(r)"]

            target = record["b.name"]

            text = (
                f"{source} {relation} {target}"
            )

            print(text)

            context.append(text)

        return "\n".join(context)

# =========================================================
# USER QUERY
# =========================================================

user_query = input(
    "\nAsk your question: "
)

# =========================================================
# SIMPLE ENTITY EXTRACTION
# =========================================================

words = re.findall(r"\w+", user_query)

entity = words[0]

# =========================================================
# RETRIEVE GRAPH CONTEXT
# =========================================================

graph_context = query_graph(entity)

# =========================================================
# FINAL RAG PROMPT
# =========================================================

final_prompt = f"""

Answer using graph knowledge.

QUESTION:
{user_query}

GRAPH CONTEXT:
{graph_context}

"""

# =========================================================
# FINAL LLM RESPONSE
# =========================================================

final_response = llm.invoke(
    [
        HumanMessage(content=final_prompt)
    ]
)

print("\n==============================")
print(" FINAL RESPONSE ")
print("==============================\n")

print(final_response.content)

# =========================================================
# CLOSE DRIVER
# =========================================================

driver.close()