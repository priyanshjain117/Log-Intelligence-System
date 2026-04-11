from typing import TypedDict, Optional

class LogState(TypedDict):
    log: str

    # Regex
    regex_label: Optional[str]

    # ML
    ml_label: Optional[str]
    ml_confidence: Optional[float]

    # Vector DB
    vector_label: Optional[str]
    vector_score: Optional[float]

    # LLM
    llm_response: Optional[str]

    # Control
    final_label: Optional[str]
    attempts: int