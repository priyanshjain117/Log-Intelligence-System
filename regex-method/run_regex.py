import json
from regex_engine import RegexEngine

INPUT_PATH = "data/processed/unified_logs.ndjson"
OUTPUT_PATH = "data/processed/regex_output.ndjson"

regex_engine = RegexEngine()

total_logs = 0
regex_matched = 0

with open(INPUT_PATH, "r") as fin, open(OUTPUT_PATH, "w") as fout:
    for line in fin:
        log = json.loads(line)
        total_logs += 1

        # Phase 1: Regex severity classification
        result = regex_engine.classify(log)

        # Always write explicit fields (no ambiguity downstream)
        log["level"] = result.get("level")
        log["confidence"] = result.get("confidence", 0.0)
        log["classified_by"] = result.get("classified_by")

        if log["classified_by"] == "regex":
            regex_matched += 1

        fout.write(json.dumps(log) + "\n")

print(
    f"[PHASE 1 COMPLETE] "
    f"Regex classified {regex_matched}/{total_logs} logs "
    f"({regex_matched / max(total_logs, 1):.2%})"
)
