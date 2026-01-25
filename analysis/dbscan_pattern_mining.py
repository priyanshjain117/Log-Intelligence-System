import json
import os
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import numpy as np
from collections import defaultdict

# -----------------------------
# Config
# -----------------------------

INPUT_FILE = "data/processed/unified_logs.json"
OUTPUT_DIR = "analysis/dbscan_clusters"

MODEL_NAME = "all-MiniLM-L6-v2"   # lightweight, fast
EPS = 0.35                       # distance threshold
MIN_SAMPLES = 20                 # minimum repeats to care

# -----------------------------
# Load logs
# -----------------------------

logs = []
messages = []

with open(INPUT_FILE) as f:
    for line in f:
        log = json.loads(line)

        # Only analyze UNKNOWN logs
        if log.get("label") is None:
            msg = log.get("clean_message")
            if msg:
                logs.append(log)
                messages.append(msg)

print(f"[INFO] Loaded {len(messages)} unlabeled logs")

if len(messages) == 0:
    raise ValueError("No unlabeled logs found. DBSCAN not needed.")

# -----------------------------
# Embed logs
# -----------------------------

print("[INFO] Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("[INFO] Generating embeddings...")
embeddings = model.encode(
    messages,
    show_progress_bar=True,
    normalize_embeddings=True
)

# -----------------------------
# DBSCAN clustering
# -----------------------------

print("[INFO] Running DBSCAN...")
dbscan = DBSCAN(
    eps=EPS,
    min_samples=MIN_SAMPLES,
    metric="cosine"
)

cluster_ids = dbscan.fit_predict(embeddings)

# -----------------------------
# Group clusters
# -----------------------------

clusters = defaultdict(list)

for idx, cluster_id in enumerate(cluster_ids):
    clusters[cluster_id].append(logs[idx])

print(f"[INFO] Found {len(clusters) - (1 if -1 in clusters else 0)} clusters")

# -----------------------------
# Save clusters for inspection
# -----------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

for cluster_id, cluster_logs in clusters.items():
    if cluster_id == -1:
        continue  # noise, ignore

    cluster_file = os.path.join(
        OUTPUT_DIR, f"cluster_{cluster_id}.txt"
    )

    with open(cluster_file, "w") as f:
        for log in cluster_logs[:100]:  # limit for readability
            f.write(log["clean_message"] + "\n")

    print(
        f"[CLUSTER {cluster_id}] "
        f"{len(cluster_logs)} logs → {cluster_file}"
    )

print("[DONE] DBSCAN pattern mining completed.")
