"""
Runs after validate_node (LLM path only).
Saves the clean_text + final label into the vector DB so future
similar logs can hit the cache instead of going all the way to the LLM.
"""
from graph.state import LogState
from nodes.vector_search_node import vector_db


def save_to_vector_node(state: LogState) -> dict:
    llm_response = state.get("llm_response") or {}

    label  = llm_response.get("label", "").strip().upper()
    reason = llm_response.get("reason", "").strip()

    # ── Fallback: if LLM exhausted retries without a valid response ───────────
    # Use ML label rather than leaving final_label empty and letting final_node
    # fall back to a low-confidence ML result with no explanation.
    if not label:
        label  = (state.get("ml_label") or "INFO").strip().upper()
        reason = (
            f"LLM failed after {state.get('attempts', 0)} attempts; "
            f"fell back to ML label (conf={state.get('ml_confidence', 0):.0%})."
        )
        source = "ml_fallback"
    else:
        source = "llm"

    # ── Persist to vector DB so next similar log hits the cache ───────────────
    clean_text = state.get("clean_text", "")
    log_vector = state.get("log_vector")

    if label and clean_text and log_vector:
        vector_db.insert(
            text      = clean_text,
            embedding = log_vector,
            label     = label,
        )

    return {
        "final_label":  label,
        "final_reason": reason,
        "final_source": source,
    }