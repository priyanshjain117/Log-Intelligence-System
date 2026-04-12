# main.py
from graph.graph import graph
from graph.state import LogState


def blank_state(log: str) -> LogState:
    return {
        "log":                 log,
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


def _color_label(label: str) -> str:
    color = _LABEL_COLORS.get(label, "")
    return f"{color}{label}{_RESET}"


def classify(log: str) -> dict:
    state = graph.invoke(blank_state(log))
    return {
        "log":      log,
        "label":    state.get("final_label")  or "UNKNOWN",
        "source":   state.get("final_source") or "unknown",
        "reason":   state.get("final_reason") or "—",
        "attempts": state.get("attempts", 0),
        "ml_conf":  state.get("ml_confidence"),
        "validated": state.get("validation_passed"),
    }


def print_result(result: dict) -> None:
    label     = result.get("label")   or "UNKNOWN"
    source    = result.get("source")  or "unknown"
    reason    = result.get("reason")  or "—"
    attempts  = result.get("attempts", 0)
    ml_conf   = result.get("ml_conf")
    validated = result.get("validated")
    log       = result.get("log", "")

    short_log = (log[:90] + "…") if len(log) > 90 else log

    # Build meta line — only show llm_attempts when LLM was actually involved
    meta_parts = [f"via {source}"]
    if ml_conf is not None:
        meta_parts.append(f"ml_conf={ml_conf:.0%}")
    if source in ("llm", "ml_fallback") and attempts > 0:
        meta_parts.append(f"llm_attempts={attempts}")
    if validated is not None:
        meta_parts.append(f"validated={'yes' if validated else 'no'}")
    meta = "  |  ".join(meta_parts)

    print(f"\n{'─' * 60}")
    print(f"  {_DIM}LOG   :{_RESET} {short_log}")
    print(f"  {_BOLD}LABEL :{_RESET} {_color_label(label)}")
    print(f"  {_DIM}META  :{_RESET} {_CYAN}{meta}{_RESET}")
    print(f"  {_DIM}REASON:{_RESET} {reason}")
    print(f"{'─' * 60}")


if __name__ == "__main__":
    logs = [
        "kernel panic: unable to handle null pointer",
        "connection refused to database",
        "check pass; user unknown",
        "sendmail[11176]: stat=Deferred: Connection refused",
        "user logged in successfully",
        "retrying request after timeout",
        "disk I/O timeout on device sda",
    ]

    print(f"\n{'=' * 60}")
    print(f"  LOG CLASSIFIER  —  {len(logs)} test logs")
    print(f"{'=' * 60}")

    for log in logs:
        result = classify(log)
        print_result(result)

    print()