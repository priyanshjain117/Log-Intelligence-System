# main.py
from dataclasses import dataclass
from typing import Optional

from graph.graph import graph
from graph.state import LogState


def blank_state(log: str, source: str = "") -> LogState:
    return {
        "log":                 log,
        "source":              source,
        "clean_text":          "",
        "log_vector":          None,
        "vector_context":      None,
        "regex_label":         None,
        "ml_label":            None,
        "ml_confidence":       None,
        "vector_label":        None,
        "vector_score":        None,
        "llm_response":        None,
        "validation_passed":   None,
        "validation_feedback": None,
        "final_label":         None,
        "final_reason":        None,
        "final_source":        None,
        "attempts":            0,
    }


# ── Label colour codes ────────────────────────────────────────────────────────
_LABEL_COLORS = {
    "CRITICAL": "\033[1;35m",   # bold magenta
    "ERROR":    "\033[1;31m",   # bold red
    "WARNING":  "\033[1;33m",   # bold yellow
    "INFO":     "\033[1;32m",   # bold green
}
_RESET = "\033[0m"
_DIM   = "\033[2m"
_BOLD  = "\033[1m"
_CYAN  = "\033[36m"
_GREEN = "\033[32m"
_RED   = "\033[31m"


@dataclass(frozen=True)
class WorkflowScenario:
    name: str
    description: str
    log: str
    source: str = ""
    expected_sources: tuple[str, ...] = ()
    warmup: bool = False


def _color_label(label: str) -> str:
    color = _LABEL_COLORS.get(label, "")
    return f"{color}{label}{_RESET}"


def classify(log: str, source: str = "") -> dict:
    state = graph.invoke(blank_state(log, source))
    return {
        "log":                 log,
        "input_source":        source or "raw",
        "label":               state.get("final_label")  or "UNKNOWN",
        "source":              state.get("final_source") or "unknown",
        "reason":              state.get("final_reason") or "-",
        "attempts":            state.get("attempts", 0),
        "ml_label":            state.get("ml_label"),
        "ml_conf":             state.get("ml_confidence"),
        "vector_label":        state.get("vector_label"),
        "vector_score":        state.get("vector_score"),
        "validated":           state.get("validation_passed"),
        "validation_feedback": state.get("validation_feedback"),
    }


def _format_confidence(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def _format_score(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _status_marker(actual: str, expected: tuple[str, ...]) -> str:
    if not expected:
        return f"{_DIM}observed{_RESET}"
    if actual in expected:
        return f"{_GREEN}matched expected path{_RESET}"
    return f"{_RED}different path observed{_RESET}"


def print_result(result: dict, scenario: Optional[WorkflowScenario] = None) -> None:
    label     = result.get("label")   or "UNKNOWN"
    source    = result.get("source")  or "unknown"
    reason    = result.get("reason")  or "—"
    attempts  = result.get("attempts", 0)
    ml_conf   = result.get("ml_conf")
    ml_label  = result.get("ml_label") or "n/a"
    vector_label = result.get("vector_label") or "n/a"
    vector_score = result.get("vector_score")
    validated = result.get("validated")
    feedback  = result.get("validation_feedback") or "n/a"
    log       = result.get("log", "")
    input_source = result.get("input_source", "raw")
    expected = scenario.expected_sources if scenario else ()

    short_log = (log[:110] + "...") if len(log) > 110 else log

    expected_text = ", ".join(expected) if expected else "any"
    validation_text = "n/a" if validated is None else ("yes" if validated else "no")
    status = _status_marker(source, expected)

    print(f"\n{'-' * 88}")
    if scenario:
        print(f"{_BOLD}{scenario.name}{_RESET}")
        print(f"{_DIM}{scenario.description}{_RESET}")
    print(f"{'-' * 88}")
    print(f"{_DIM}Input source :{_RESET} {input_source}")
    print(f"{_DIM}Log          :{_RESET} {short_log}")
    print(f"{_DIM}Expected path:{_RESET} {expected_text}")
    print(f"{_DIM}Actual path  :{_RESET} {_CYAN}{source}{_RESET} ({status})")
    print(f"{_BOLD}Final label  :{_RESET} {_color_label(label)}")
    print(f"{_DIM}Reason       :{_RESET} {reason}")
    print()
    print(f"{_DIM}Signals      :{_RESET} ml_label={ml_label} | ml_conf={_format_confidence(ml_conf)}")
    print(f"{_DIM}Vector       :{_RESET} vector_label={vector_label} | vector_score={_format_score(vector_score)}")
    print(f"{_DIM}LLM/validate :{_RESET} attempts={attempts} | validated={validation_text} | feedback={feedback}")


def run_scenario(scenario: WorkflowScenario) -> dict:
    if scenario.warmup:
        print(f"\n{_DIM}Warming vector cache for: {scenario.name}{_RESET}")
        classify(scenario.log, scenario.source)
    result = classify(scenario.log, scenario.source)
    print_result(result, scenario)
    return result


def workflow_scenarios() -> list[WorkflowScenario]:
    return [
        WorkflowScenario(
            name="Scenario 1 - Regex fast path",
            description="A source-aware Linux auth pattern should be classified by the regex layer.",
            source="linux",
            log="check pass; user unknown",
            expected_sources=("regex",),
        ),
        WorkflowScenario(
            name="Scenario 2 - ML confidence path",
            description="A common semantic log should be handled by ML if the classifier is confident enough.",
            log="user logged in successfully",
            expected_sources=("ml",),
        ),
        WorkflowScenario(
            name="Scenario 3 - LLM fallback and validation path",
            description="An ambiguous operational issue should pass through ML/vector checks and use the LLM path if confidence is low.",
            log="kernel panic: unable to handle null pointer dereference in interrupt context",
            expected_sources=("llm", "ml_fallback"),
        ),
        WorkflowScenario(
            name="Scenario 4 - Vector cache path",
            description="The same low-confidence log is classified once to warm the in-memory FAISS cache, then classified again to demonstrate cache reuse.",
            log="kernel panic: unable to handle null pointer dereference in interrupt context",
            expected_sources=("vector_cache",),
            warmup=True,
        ),
        WorkflowScenario(
            name="Scenario 5 - Critical severity example",
            description="A severe system failure example demonstrates the final severity formatting and reasoning output.",
            source="bgl",
            log="generating core.123 after fatal application failure",
            expected_sources=("regex",),
        ),
    ]


if __name__ == "__main__":
    scenarios = workflow_scenarios()

    print(f"\n{'=' * 88}")
    print(f"  LOG INTELLIGENCE SYSTEM - WORKFLOW SCENARIO DEMO")
    print(f"{'=' * 88}")
    print("  Each scenario shows the intended workflow branch and the actual branch used.")
    print("  ML, vector, and LLM paths depend on local model artifacts, cache state, and API access.")

    results = [run_scenario(scenario) for scenario in scenarios]

    print(f"\n{'=' * 88}")
    print("  SUMMARY")
    print(f"{'=' * 88}")
    for scenario, result in zip(scenarios, results):
        actual = result.get("source", "unknown")
        expected = scenario.expected_sources
        status = "OK" if not expected or actual in expected else "CHECK"
        print(f"  {status:<5} {scenario.name:<45} -> {actual}")

    print()
