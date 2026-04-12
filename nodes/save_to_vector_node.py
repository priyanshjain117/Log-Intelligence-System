"""
Runs after validate_node passes (LLM path only).
Saves clean_text + final label into the vector DB so future
logs can hit the cache instead of going all the way to the LLM.
"""
from graph.state import LogState
from nodes.vector_search_node import vector_db


def save_to_vector_node(state: LogState) -> dict:
    llm_response = state.get("llm_response") or {}
    label = llm_response.get("label", "").strip().upper()
    reason = llm_response.get("reason", "")
    clean_text = state.get("clean_text", "")
    log_vector = state.get("log_vector")

    if label and clean_text and log_vector:
        vector_db.insert(
            text=clean_text,
            embedding=log_vector,
            label=label,
        )

    return {
        "final_label": label,
        "final_reason": reason,
    }