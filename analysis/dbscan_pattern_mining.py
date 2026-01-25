import json
import os
from collections import defaultdict, Counter

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN


INPUT_FILE = "./unified_logs.ndjson"   # NDJSON
OUTPUT_DIR = "analysis/regex_candidates"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# DBSCAN parameters
EPS = 0.3             # semantic similarity threshold
MIN_SAMPLES = 30        # frequency threshold for regex-worthiness

# How many samples to show per cluster
MAX_EXAMPLES = 50

# STEP 1: LOAD UNLABELED LOGS ONLY

logs = []
messages = []

with open(INPUT_FILE) as f:
    for line in f:
        log = json.loads(line)

        # Only logs NOT already handled by regex
        if log.get("label") is None:
            msg = log.get("clean_message")
            if msg:
                logs.append(log)
                messages.append(msg)

print(f"[INFO] Unlabeled logs loaded: {len(messages)}")

if len(messages) < MIN_SAMPLES:
    raise RuntimeError("Not enough unlabeled logs to justify DBSCAN.")

# =====================================================
# STEP 2: EMBEDDINGS (SEMANTIC, NOT STRING)
# =====================================================

print("[INFO] Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)

print("[INFO] Encoding log messages...")
embeddings = model.encode(
    messages,
    show_progress_bar=True,
    normalize_embeddings=True
)

# =====================================================
# STEP 3: DBSCAN — FIND REPEATED PATTERNS
# =====================================================

print("[INFO] Running DBSCAN...")
dbscan = DBSCAN(
    eps=EPS,
    min_samples=MIN_SAMPLES,
    metric="cosine"
)

cluster_ids = dbscan.fit_predict(embeddings)

# =====================================================
# STEP 4: GROUP CLUSTERS
# =====================================================

clusters = defaultdict(list)

for idx, cid in enumerate(cluster_ids):
    clusters[cid].append(logs[idx])

num_real_clusters = len([c for c in clusters if c != -1])

print(f"[INFO] Found {num_real_clusters} candidate clusters")

# =====================================================
# STEP 5: SAVE ONLY REGEX-WORTHY CLUSTERS
# =====================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

for cid, cluster_logs in clusters.items():
    if cid == -1:
        continue  # noise → BERT/LLM handles this

    freq = len(cluster_logs)

    # Explicit frequency gate (your requirement)
    if freq < MIN_SAMPLES:
        continue

    out_path = os.path.join(
        OUTPUT_DIR, f"cluster_{cid}_freq_{freq}.txt"
    )

    with open(out_path, "w") as f:
        for log in cluster_logs[:MAX_EXAMPLES]:
            f.write(log["clean_message"] + "\n")

    print(
        f"[CANDIDATE] cluster={cid} "
        f"freq={freq} → {out_path}"
    )

print("[DONE] DBSCAN regex pattern mining complete.")
