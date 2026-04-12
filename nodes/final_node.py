"""
Resolves the final label from whichever path produced it
(regex, ML, vector cache, or LLM) and emits the finished state.
"""
from graph.state import LogState


def final_node(state: LogState) -> dict:
    # Each node stamps final_source when it produces a confident result.
    # We trust that value first, then fall back to deriving from label keys.

    resolved_label = state.get("final_label")
    source         = state.get("final_source")
    reason         = state.get("final_reason")

    # ── Derive source + label if not already stamped ──────────────────────────
    if not resolved_label or not source:
        _PRIORITY = [
            ("regex_label",  "regex"),
            ("ml_label",     "ml"),
            ("vector_label", "vector_cache"),
        ]
        for key, src in _PRIORITY:
            val = state.get(key)
            if val:
                resolved_label = val.strip().upper()
                source = src
                break

    # ── LLM path: extract label + reason from llm_response ───────────────────
    if source == "llm" or not resolved_label:
        llm_response = state.get("llm_response")
        if isinstance(llm_response, dict):
            llm_label  = llm_response.get("label", "").strip().upper()
            llm_reason = llm_response.get("reason", "").strip()
            if llm_label:
                resolved_label = llm_label
                source         = "llm"
                reason         = llm_reason or reason

    # ── Build reason if still missing ────────────────────────────────────────
    if not reason:
        reason = _build_reason(source, state)

    # ── Last resort ───────────────────────────────────────────────────────────
    if not resolved_label:
        resolved_label = "INFO"
        source         = "fallback"
        reason         = "No confident signal found; defaulting to INFO."

    print(
        f"[final_node] label={resolved_label} | source={source} "
        f"| attempts={state.get('attempts', 0)} | reason={reason}"
    )

    return {
        "final_label":  resolved_label,
        "final_source": source,
        "final_reason": reason,
    }


def _build_reason(source: str, state: LogState) -> str:
    if source == "regex":
        return "Matched a high-confidence regex pattern."
    if source == "ml":
        conf = state.get("ml_confidence", 0)
        return f"ML model predicted with {conf:.0%} confidence."
    if source == "vector_cache":
        score = state.get("vector_score", 0)
        return f"Vector cache hit — similarity score {score:.2f}."
    if source == "llm":
        # Reason should have been captured above; this is a true fallback.
        return "LLM classified (reason not returned by model)."
    return "Classification source unknown."