import json
from regex_engine import RegexEngine

INPUT = "data/processed/unified_logs.ndjson"
OUTPUT = "data/processed/regex_output.ndjson"

engine = RegexEngine()

matched = 0
total = 0

with open(INPUT) as fin, open(OUTPUT, "w") as fout:
    for line in fin:
        log = json.loads(line)
        total += 1

        result = engine.classify(log)

        log["label"] = result["label"]
        log["confidence"] = result["confidence"]
        log["classified_by"] = result["stage"]

        if result["label"]:
            matched += 1

        fout.write(json.dumps(log) + "\n")

print(f"[DONE] Phase 1 complete — {matched}/{total} logs matched by regex")
