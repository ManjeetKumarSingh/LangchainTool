import networkx as nx

# =====================================================
# GRAPH
# =====================================================

graph = nx.Graph()

# =====================================================
# ENTITIES
# =====================================================

graph.add_node("Kafka")

graph.add_node("Zookeeper")

graph.add_node("LangGraph")

graph.add_node("Qdrant")

# =====================================================
# RELATIONSHIPS
# =====================================================

graph.add_edge(
    "Kafka",
    "Zookeeper",
    relation="uses"
)

graph.add_edge(
    "LangGraph",
    "Qdrant",
    relation="retrieves_from"
)

# =====================================================
# PRINT RELATIONS
# =====================================================

for edge in graph.edges(data=True):

    print(edge)