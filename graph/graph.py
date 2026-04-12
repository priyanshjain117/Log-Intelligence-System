from langgraph.graph import StateGraph, END

from graph.state import LogState
from nodes.router import route_from_regex, route_from_ml, route_from_vector, should_retry

from nodes.regex_node import regex_node
from nodes.ml_node import ml_node
from nodes.vector_search_node import vector_search_node
from nodes.llm_node import llm_node
from nodes.validate_node import validate_node
from nodes.save_to_vector_node import save_to_vector_node
from nodes.final_node import final_node


def build_graph() -> StateGraph:
    builder = StateGraph(LogState)

    builder.add_node("regex_node",regex_node)
    builder.add_node("ml_node",ml_node)
    builder.add_node("vector_search_node",vector_search_node)
    builder.add_node("llm_node",llm_node)
    builder.add_node("validate_node",validate_node)
    builder.add_node("save_to_vector_node",save_to_vector_node)
    builder.add_node("final_node",final_node)

    builder.set_entry_point("regex_node")

    builder.add_conditional_edges(
        "regex_node",
        route_from_regex,
        {"final_node": "final_node", "ml_node": "ml_node"},
    )

    builder.add_conditional_edges(
        "ml_node",
        route_from_ml,
        {"final_node": "final_node", "vector_search_node": "vector_search_node"},
    )

    builder.add_conditional_edges(
        "vector_search_node",
        route_from_vector,
        {"final_node": "final_node", "llm_node": "llm_node"},
    )

    builder.add_edge("llm_node", "validate_node")

    builder.add_conditional_edges(
        "validate_node",
        should_retry,
        {
            "save_to_vector_node": "save_to_vector_node",
            "llm_node":            "llm_node",
        },
    )

    # save always flows into final
    builder.add_edge("save_to_vector_node", "final_node")
    builder.add_edge("final_node", END)

    return builder.compile()


graph = build_graph()