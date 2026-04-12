from utils import load_ml_model, load_label_encoder
from graph.state import LogState
from utils.clean import prepare_for_ml
from utils.loader import load_embedding_model

ml_model=load_ml_model()
label_encoder=load_label_encoder()
embedding_model=load_embedding_model()

def ml_node(state: LogState):
    log=state['log']

    log=prepare_for_ml(log)

    if not log:
        return {
            "ml_label": None,
            "ml_confidence": 0.0,
            "log_vector": None
        }

    log_vector = embedding_model.encode([log])
    probs = ml_model.predict_proba(log_vector)  
    probs = probs[0]

    label_id = probs.argmax()
    
    confidence = float(probs[label_id])
    label = label_encoder.inverse_transform([label_id])[0]

    return {
        "log_vector": log_vector[0].tolist(),  # convert to list for JSON serialization
        "ml_label": label,
        "ml_confidence": confidence,
    }
