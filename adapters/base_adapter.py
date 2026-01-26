from abc import ABC, abstractmethod
import re

class BaseAdapter(ABC):
    """
    Abstract base class for all log adapters.
    Every adapter MUST return a unified log schema.
    """

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def parse(self, raw_log: str) -> dict:
        """
        Parse a raw log line into unified schema.
        """
        pass

    # ---------- Common Utilities ----------

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for ML consumption.
        """
        text = text.lower()
        text = re.sub(r"\b\d+\b", "<NUM>", text)
        text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<IP>", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def detect_log_level(self, text: str) -> str:
        """
        Extract log level using simple heuristics.
        """
        levels = ["ERROR", "WARN", "INFO", "DEBUG"]
        for level in levels:
            if level.lower() in text.lower():
                return level
        return "UNKNOWN"

    def base_output(self, raw_log: str, clean_message: str,
                    log_level: str = "UNKNOWN",
                    service: str = None,
                    timestamp: str = None,
                    structured_fields: dict = None) -> dict:

        return {
            "source": self.source_name,
            "raw_log": raw_log,
            "clean_message": clean_message,
            "log_level": log_level,
            "service": service,
            "timestamp": timestamp,
            "structured_fields": structured_fields or {},
        }