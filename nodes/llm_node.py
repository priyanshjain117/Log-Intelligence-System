# graph/nodes/llm_node.py
from graph.state import LogState
from utils.llm import getLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

VALID_LABELS = ["ERROR", "WARNING", "INFO", "CRITICAL"]

llm = getLLM()
parser = JsonOutputParser()

_PROMPT = PromptTemplate.from_template(
    """You are an expert log classification system. Your task is to assign the most accurate severity label to the log entry below.

## Valid labels
{valid_labels}

## Log entry
{clean_text}

## ML model suggestion
Label: {ml_label} | Confidence: {ml_conf:.0%}

## Similar logs (RAG context)
{context_text}

## Instructions
- Choose exactly ONE label from the valid labels list.
- Your reason must explain the key signal(s) in the log that justify the label (1–2 sentences).
- If the ML suggestion is high-confidence (≥ 0.85) and fits the evidence, prefer it.
- Ignore the ML suggestion if the log content clearly contradicts it.

Respond with ONLY valid JSON — no markdown fences, no extra keys.

{{
  "label": "<ONE_OF_THE_VALID_LABELS>",
  "reason": "<your concise justification>"
}}"""
)

chain = _PROMPT | llm | parser


def llm_node(state: LogState) -> dict:
    clean_text = state.get("clean_text", "")
    ml_label = state.get("ml_label", "UNKNOWN")
    ml_conf = state.get("ml_confidence", 0.0)
    vector_context = state.get("vector_context", [])
    attempts = state.get("attempts", 0)

    context_text = (
        "\n".join(f"- {item['text']} → {item['label']}" for item in vector_context)
        if vector_context
        else "No similar logs found."
    )

    result: dict = chain.invoke({
        "valid_labels": ", ".join(VALID_LABELS),
        "clean_text": clean_text,
        "ml_label": ml_label,
        "ml_conf": ml_conf,
        "context_text": context_text,
    })

    return {
        "llm_response": result,          # { "label": "ERROR", "reason": "…" }
        "attempts": attempts + 1,
    }
