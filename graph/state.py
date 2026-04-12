from typing import TypedDict, Optional, Any

class LogState(TypedDict):
    log: str
    clean_text: Optional[str]          # Added
    log_vector: Optional[list[float]]  

    # Regex
    regex_label: Optional[str]

    # ML
    ml_label: Optional[str]
    ml_confidence: Optional[float]

    # Vector DB
    vector_label: Optional[str]
    vector_score: Optional[float]
    vector_context: Optional[list]     # Added

    # LLM
    llm_response: Optional[dict]       # Changed to dict (or Any)

    validation_passed: Optional[bool]
    validation_feedback: Optional[str]

    # Control
    final_label: Optional[str]
    final_source: Optional[str]        # Added
    final_reason: Optional[str]        # Added
    attempts: int