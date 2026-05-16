## Architecture of the KnowledgeGraph RAG

```
Documents
   ↓
Chunking
   ↓
Entity Extraction
   ↓
Relationship Extraction
   ↓
Knowledge Graph
   ↓
Graph Retrieval
   ↓
LLM

```

## Steps Involve in it 
- `RecursiveCharacterTextSplitter` : Normal as usual chunkings
- `Use LLM or NLP` : For Entity Extractions 
     - Example entities:

            * Kafka
            * LangGraph
            * Qdrant
            * Zookeeper

- ` For Extracting Relationship ` : Relationship Extraction 

  ```
      Kafka -> uses -> Zookeeper

  ```
-  ` Storing these in GraphDB` : GraphDB List 

      - Usually:

            * Neo4j
            * NebulaGraph
            * ArangoDB
            * TigerGraph
- ` Query To Graph`
   ```
      Find systems related to Kafka
   ```

- `Send Context To LLM`

  - LLM now receives:

            * graph relations
            * semantic context
            * retrieved chunks