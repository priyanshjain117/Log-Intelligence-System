from graph.state import LogState
from utils.llm import getLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

VALID_LABELS = ["ERROR", "WARNING", "INFO", "CRITICAL"]
MAX_ATTEMPTS = 3

llm = getLLM()
parser = JsonOutputParser()

_JUDGE_PROMPT = PromptTemplate.from_template(
    """You are a strict quality-control judge for a log classification system.

Evaluate the classification below and return a JSON verdict.

## Classification to evaluate
Log: {clean_text}
Assigned label: {label}
Reason given: {reason}

## Rules
1. `label` must be one of: {valid_labels}
2. `reason` must be non-empty and actually reference content from the log.
3. The label must be consistent with the reason.

Respond ONLY with valid JSON:
{{
  "valid": true | false,
  "feedback": "<one sentence — what is wrong, or 'OK' if valid>"
}}"""
)

judge_chain = _JUDGE_PROMPT | llm | parser


def validate_node(state: LogState) -> dict:
    llm_response = state.get("llm_response", {})
    label = llm_response.get("label", "").strip().upper()
    reason = llm_response.get("reason", "").strip()

    verdict: dict = judge_chain.invoke({
        "clean_text": state.get("clean_text", ""),
        "label": label,
        "reason": reason,
        "valid_labels": ", ".join(VALID_LABELS),
    })

    is_valid = (
        verdict.get("valid", False)
        and label in VALID_LABELS
        and bool(reason)
    )

    return {
        "validation_passed": is_valid,
        "validation_feedback": verdict.get("feedback", ""),
    }
