from utils import load_ml_model, load_label_encoder
from graph.state import LogState

ml_model=load_ml_model()
label_encoder=load_label_encoder()

def ml_node(state: LogState):
    log=state['log']

    probs = ml_model.predict_proba([log])  
    probs = probs[0]
    
    label_id = probs.argmax()
    
    confidence = float(probs[label_id])
    label = label_encoder.inverse_transform([label_id])[0]

    return {
        "ml_label": label,
        "ml_confidence": confidence,
    }
