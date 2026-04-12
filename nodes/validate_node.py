import json
import re

from graph.state import LogState
from utils.llm import getLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

VALID_LABELS = ["ERROR", "WARNING", "INFO", "CRITICAL"]
MAX_ATTEMPTS = 3

llm    = getLLM()
parser = JsonOutputParser()

# The judge only checks label-reason CONSISTENCY.
# Label validity is checked in Python — never delegated to the LLM.
_JUDGE_PROMPT = PromptTemplate.from_template(
    """You are reviewing a log classification. Answer only: does the reason make sense for this label and log?

Log:    {clean_text}
Label:  {label}
Reason: {reason}

Reply with ONLY valid JSON — no markdown:
{{"consistent": true, "feedback": "OK"}}

Only set consistent=false if the reason CLEARLY contradicts the label (e.g. reason says "successful" but label is ERROR).
When in doubt, return consistent=true."""
)

judge_chain = _JUDGE_PROMPT | llm | parser


def validate_node(state: LogState) -> dict:
    llm_response = state.get("llm_response") or {}

    if isinstance(llm_response, str):
        try:
            llm_response = json.loads(re.sub(r"```json|```", "", llm_response).strip())
        except Exception:
            llm_response = {}

    label  = llm_response.get("label", "").strip().upper()
    reason = llm_response.get("reason", "").strip()

    # ── Hard Python checks — never ask the LLM about these ───────────────────
    if not label or label not in VALID_LABELS:
        msg = f"label {label!r} not in {VALID_LABELS}"
        print(f"[validate_node] HARD FAIL | {msg}")
        return {"validation_passed": False, "validation_feedback": msg}

    if not reason:
        msg = "reason is empty"
        print(f"[validate_node] HARD FAIL | {msg}")
        return {"validation_passed": False, "validation_feedback": msg}

    # ── LLM judge — only checks consistency, not label validity ──────────────
    try:
        verdict = judge_chain.invoke({
            "clean_text": state.get("clean_text", "") or state.get("log", ""),
            "label":      label,
            "reason":     reason,
        })

        print(f"[validate_node] raw verdict type={type(verdict).__name__} value={verdict}")

        if isinstance(verdict, str):
            verdict = json.loads(re.sub(r"```json|```", "", verdict).strip())

        if not isinstance(verdict, dict):
            raise ValueError(f"Unexpected verdict shape: {verdict}")

        # Accept both "consistent" and "valid" keys from the judge
        is_consistent = verdict.get("consistent", verdict.get("valid", True))
        feedback      = verdict.get("feedback", "OK")

    except Exception as e:
        print(f"[validate_node] judge error: {e} — accepting label as-is")
        is_consistent = True
        feedback      = "OK (judge failed — accepted)"

    is_valid = bool(is_consistent)

    print(f"[validate_node] label={label} | valid={is_valid} | feedback={feedback!r}")

    return {
        "validation_passed":   is_valid,
        "validation_feedback": feedback,
    }