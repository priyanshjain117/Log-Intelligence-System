# 1. Imports
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

from sentence_transformers import SentenceTransformer
import joblib


# 2. Load Dataset
df = pd.read_csv("../data/merged_logs.csv")

# 3. Basic Cleaning
df = df.dropna(subset=["clean_message", "level"])

# Keep only needed columns
df = df[["clean_message", "level"]]

# Rename for clarity
df.columns = ["text", "label"]

print("Sample Data:")
print(df.head())

# 4. Encode Labels
labels = df["label"].unique()
label2id = {label: idx for idx, label in enumerate(labels)}
id2label = {idx: label for label, idx in label2id.items()}

df["label_id"] = df["label"].map(label2id)

# 5. Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    df["text"],
    df["label_id"],
    test_size=0.2,
    random_state=42,
    stratify=df["label_id"]
)

# 6. Load Sentence Transformer
model = SentenceTransformer("all-MiniLM-L6-v2")

# 7. Convert Text → Embeddings
print("Encoding training data...")
X_train_emb = model.encode(X_train.tolist(), show_progress_bar=True)

print("Encoding test data...")
X_test_emb = model.encode(X_test.tolist(), show_progress_bar=True)

# 8. Train Classifier
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train_emb, y_train)

# 9. Evaluation
y_pred = clf.predict(X_test_emb)

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, target_names=id2label.values()))

# 10. Save Everything
joblib.dump(clf, "log_classifier.pkl")
joblib.dump(label2id, "label_mapping.pkl")

print("\nModel saved successfully!")