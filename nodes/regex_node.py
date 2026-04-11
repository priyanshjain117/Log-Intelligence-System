from graph.state import LogState
from regex_method.regex_engine import regex_engine

def regex_node(state: LogState):
    log = state["log"]

    result = regex_engine.classify(log)

    level = result.get("level")
    confidence = result.get("confidence", 0.0)

    # If regex matched
    if level:
        return {
            "regex_label": level,
            "final_label": level  
        }

    # If not matched
    return {
        "regex_label": None,
    }
