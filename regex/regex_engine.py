import re
from regex_rules import REGEX_RULES

class RegexEngine:
    def __init__(self):
        self.rules = [
            {**rule, "compiled": re.compile(rule["pattern"], re.IGNORECASE)}
            for rule in REGEX_RULES
        ]

    def classify(self, log):
        text = log["clean_message"]
        source = log["source"]

        for rule in self.rules:
            if source not in rule["sources"]:
                continue

            if rule["compiled"].search(text):
                return {
                    "label": rule["label"],
                    "confidence": rule["confidence"],
                    "stage": "regex"
                }

        return {
            "label": None,
            "confidence": 0.0,
            "stage": "Unclassified"
        }
