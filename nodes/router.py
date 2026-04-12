from graph.state import LogState

def route_from_regex(state: LogState):
    if state.get("regex_label"):
        return "final_node"
    return "ml_node"

def route_from_ml(state: LogState):
    confidence = state.get("ml_confidence", 0)

    if confidence >= 0.85:
        return "final_node"
    else:
        return "vector_search_node"  
    
def route_from_vector(state: LogState):
    score = state.get("vector_score", 0.0)

    if score >= 0.9:
        return "final_node"

    return "llm_node"