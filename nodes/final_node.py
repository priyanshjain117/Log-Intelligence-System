"""
Resolves the final label from whichever path produced it
(regex, ML, vector cache, or LLM) and emits the finished state.
"""
from graph.state import LogState


_SOURCE_PRIORITY = [
    # (state_key_for_label, source_name)
    ("regex_label",   "regex"),
    ("ml_label",      "ml"),
    ("vector_label",  "vector_cache"),
    ("final_label",   "llm"),   # set by save_to_vector_node (LLM path)
]


def final_node(state: LogState) -> dict:
    # Walk priority order; first non-None label wins.
    # For the LLM path, final_label is already set by save_to_vector_node.
    # For regex/ML/vector paths, final_label may already be set by the router
    # (regex_node sets it directly; we also handle ml/vector here).

    resolved_label = state.get("final_label")
    source = "llm"

    if not resolved_label:
        for key, src in _SOURCE_PRIORITY:
            val = state.get(key)
            if val:
                resolved_label = val.strip().upper()
                source = src
                break

    reason = state.get("final_reason") or _default_reason(source, state)

    print(
        f"[final_node] label={resolved_label} | source={source} "
        f"| attempts={state.get('attempts', 0)} | reason={reason}"
    )

    return {
        "final_label": resolved_label,
        "final_reason": reason,
    }


def _default_reason(source: str, state: LogState) -> str:
    if source == "regex":
        return "Matched a regex pattern with high confidence."
    if source == "ml":
        conf = state.get("ml_confidence", 0)
        return f"ML model predicted with {conf:.0%} confidence."
    if source == "vector_cache":
        score = state.get("vector_score", 0)
        return f"Vector cache hit with similarity score {score:.2f}."
    return "LLM classification (no reason captured)."