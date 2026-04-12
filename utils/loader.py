import joblib
from dotenv import load_dotenv
import os

from sentence_transformers import SentenceTransformer
load_dotenv()

model_path = os.getenv("ML_MODEL_PATH", "models/ml_model.joblib")
label_encoder_path = os.getenv("LABEL_ENCODER_PATH", "models/label_encoder.joblib")
embedding_model = "all-MiniLM-L6-v2"


def load_ml_model():
    return joblib.load(model_path)

def load_label_encoder():
    return joblib.load(label_encoder_path)
 
def load_embedding_model():
    return SentenceTransformer(embedding_model)
