from graph.state import LogState
from nodes.validate_node import MAX_ATTEMPTS


def route_from_regex(state: LogState) -> str:
    if state.get("regex_label"):
        return "final_node"
    return "ml_node"


def route_from_ml(state: LogState) -> str:
    confidence = state.get("ml_confidence", 0.0)
    if confidence >= 0.85:
        # Stamp final_label so final_node doesn't need to re-derive it
        return "final_node"
    return "vector_search_node"


def route_from_vector(state: LogState) -> str:
    score = state.get("vector_score", 0.0)
    if score >= 0.9:
        return "final_node"
    return "llm_node"


def should_retry(state: LogState) -> str:
    if state.get("validation_passed"):
        return "save_to_vector_node"          # ← goes to save first, then final
    if state.get("attempts", 0) < MAX_ATTEMPTS:
        return "llm_node"
    return "save_to_vector_node"              # best-effort save even on exhaustion