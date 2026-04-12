import joblib
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer

load_dotenv()

ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "model/svm_classifier.pkl")
LABEL_ENCODER_PATH = os.getenv("LABEL_ENCODER_PATH", "model/label_encoder.pkl")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_ml_model():
    path = os.path.join(BASE_DIR, ML_MODEL_PATH)
    return joblib.load(path)


def load_label_encoder():
    path = os.path.join(BASE_DIR, LABEL_ENCODER_PATH)
    return joblib.load(path)


def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)
