from utils.vector_db import VectorDB
from .ml_node import embedding_model

dim = len(embedding_model.encode(["test"])[0])

vector_db = VectorDB(dim)


def vector_search_node(state):
    vector = state.get("log_vector")

    if vector is None:
        return {
            "vector_label":   None,
            "vector_score":   0.0,
            "vector_context": [],
        }

    results = vector_db.search(vector)

    if not results:
        return {
            "vector_label":   None,
            "vector_score":   0.0,
            "vector_context": [],
        }

    best = results[0]

    return {
        "vector_label":   best["label"],
        "vector_score":   best["score"],
        "vector_context": results,        # ← passed to llm_node as RAG context
        "final_label":    best["label"],
        "final_source":   "vector_cache",
    }
