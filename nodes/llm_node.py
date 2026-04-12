import json
import re

from graph.state import LogState
from utils.llm import getLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

VALID_LABELS = ["ERROR", "WARNING", "INFO", "CRITICAL"]

llm = getLLM()
parser = JsonOutputParser()

_PROMPT = PromptTemplate.from_template(
    """You are an expert log classification system. Assign the most accurate severity label to the log entry below.

## Valid labels
{valid_labels}

## Log entry
{clean_text}

## ML model suggestion
Label : {ml_label}
Confidence: {ml_conf:.0%}

## Similar logs (RAG context)
{context_text}

## Instructions
- Choose exactly ONE label from this list: {valid_labels}
- Write a reason that directly references specific words or patterns from the log entry.
- If ML confidence >= 0.85 and fits the log, prefer that label.
- Do NOT write vague reasons like "potential issue" or "non-issue" — be specific.

Respond with ONLY this JSON, no markdown, no extra text:
{{"label": "ERROR", "reason": "Specific explanation referencing the log."}}"""
)

chain = _PROMPT | llm | parser


def llm_node(state: LogState) -> dict:
    attempts       = state.get("attempts", 0)
    clean_text     = state.get("clean_text", "") or state.get("log", "")
    ml_label       = state.get("ml_label", "UNKNOWN")
    ml_conf        = state.get("ml_confidence", 0.0)
    vector_context = state.get("vector_context") or []

    print(f"\n{'='*50}")
    print(f"[llm_node] attempt={attempts + 1}")
    print(f"[llm_node] clean_text={clean_text[:80]!r}")
    print(f"[llm_node] ml_label={ml_label} | ml_conf={ml_conf:.0%}")
    print(f"{'='*50}")

    context_text = (
        "\n".join(f"- {item['text']} -> {item['label']}" for item in vector_context)
        if vector_context
        else "No similar logs found."
    )

    try:
        raw = chain.invoke({
            "valid_labels": ", ".join(VALID_LABELS),
            "clean_text":   clean_text,
            "ml_label":     ml_label,
            "ml_conf":      ml_conf,
            "context_text": context_text,
        })

        print(f"[llm_node] raw type={type(raw).__name__} value={raw}")

        if isinstance(raw, str):
            raw = json.loads(re.sub(r"```json|```", "", raw).strip())

        if not isinstance(raw, dict) or "label" not in raw:
            raise ValueError(f"Bad response shape: {raw}")

        raw["label"] = raw["label"].strip().upper()

        if raw["label"] not in VALID_LABELS:
            raise ValueError(f"Invalid label returned: {raw['label']!r}")

        result = raw
        print(f"[llm_node] OK label={result['label']} reason={result.get('reason','')!r}")

    except Exception as e:
        print(f"[llm_node] ERROR on attempt {attempts + 1}: {e}")
        result = {
            "label":  ml_label if ml_label in VALID_LABELS else "INFO",
            "reason": f"LLM failed on attempt {attempts + 1}: {e}",
        }

    return {
        "llm_response": result,
        "attempts":     attempts + 1,
        "final_source": "llm",
    }