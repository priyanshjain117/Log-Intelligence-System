import joblib
from dotenv import load_dotenv
import os

load_dotenv()

model_path = os.getenv("ML_MODEL_PATH", "models/ml_model.joblib")
label_encoder_path = os.getenv("LABEL_ENCODER_PATH", "models/label_encoder.joblib")

def load_ml_model():
    return joblib.load(model_path)

def load_label_encoder():
    return joblib.load(label_encoder_path)
