import re
from .regex_rules import REGEX_RULES


class RegexEngine:
    def __init__(self):
        # Compile regex patterns once (fast + production-safe)
        self.rules = [
            {
                **rule,
                "compiled": re.compile(rule["pattern"], re.IGNORECASE)
            }
            for rule in REGEX_RULES
        ]

    def classify(self, log: dict) -> dict:
        """
        Phase 1: Regex-based severity classification.

        Returns:
            {
                "level": <LEVEL or None>,
                "confidence": <float>,
                "classified_by": "regex" | "Unclassified"
            }
        """
        text = log.get("clean_message", "")
        source = log.get("source")

        for rule in self.rules:
            if source and source not in rule["sources"]:
                continue

            if rule["compiled"].search(text):
                return {
                    "level": rule["level"],
                    "confidence": rule["confidence"],
                    "classified_by": "regex"
                }

        # Explicitly unresolved — hand off to Phase 2
        return {
            "level": None,
            "confidence": 0.0,
            "classified_by": "Unclassified"
        }
