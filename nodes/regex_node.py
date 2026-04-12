from graph.state import LogState
from regex_method.regex_engine import RegexEngine

regex_engine = RegexEngine()

def regex_node(state: LogState):
    log = state["log"]
    if isinstance(log, str):
        log = {
            "clean_message": log,
            "source": state.get("source", "") 
        }
    result = regex_engine.classify(log)

    level = result.get("level")
    confidence = result.get("confidence", 0.0)

    # If regex matched
    if level:
        return {
            "regex_label": level,
            "final_label": level,
            "final_source": "regex"
        }

    # If not matched
    return {
        "regex_label": None,
        "final_label": None,
        "final_source": None
    }
