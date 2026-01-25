import json
import os
from adapters.generic_adapter import GenericAdapter
from adapters.apache_adapter import ApacheAdapter
from adapters.linux_adapter import LinuxAdapter
from adapters.mac_adapter import MacAdapter
from adapters.hdfs_adapter import HDFSAdapter
from adapters.bgl_adapter import BGLAdapter

# -------------------------------
# Adapter registry
# -------------------------------

ADAPTERS = {
    "apache": ApacheAdapter(),
    "linux": LinuxAdapter(),
    "mac": MacAdapter(),
    "hdfs": HDFSAdapter(),
    "bgl": BGLAdapter(),
}

generic_adapter = GenericAdapter()

# -------------------------------
# Core processing logic
# -------------------------------

def process_file(file_path: str, source: str):
    """
    Process a single log file and return list of unified log objects.
    """
    adapter = ADAPTERS.get(source, generic_adapter)
    processed_logs = []

    with open(file_path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                log_obj = adapter.parse(line)
            except Exception:
                # Absolute safety net
                log_obj = generic_adapter.parse(line)

            processed_logs.append(log_obj)

    return processed_logs


def process_dataset(root_dir="data/raw", output_file="data/processed/unified_logs.json"):
    """
    Walk through all datasets and build unified_logs.json
    """
    all_logs = []

    for source in os.listdir(root_dir):
        source_path = os.path.join(root_dir, source)

        if not os.path.isdir(source_path):
            continue

        print(f"[INFO] Processing source: {source}")

        for file_name in os.listdir(source_path):
            file_path = os.path.join(source_path, file_name)

            if not os.path.isfile(file_path):
                continue

            logs = process_file(file_path, source)
            all_logs.extend(logs)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        for log in all_logs:
            f.write(json.dumps(log) + "\n")

    print(f"[DONE] Wrote {len(all_logs)} logs to {output_file}")


if __name__ == "__main__":
    process_dataset()
