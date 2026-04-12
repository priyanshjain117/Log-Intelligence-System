from utils.loader import load_ml_model, load_label_encoder, load_embedding_model
from graph.state import LogState
from utils.clean import prepare_for_ml

ml_model        = load_ml_model()
label_encoder   = load_label_encoder()
embedding_model = load_embedding_model()


def ml_node(state: LogState):
    raw_log    = state["log"]
    clean_text = prepare_for_ml(raw_log)   # ← capture cleaned text

    if not clean_text:
        return {
            "clean_text":    "",
            "ml_label":      None,
            "ml_confidence": 0.0,
            "log_vector":    None,
        }

    log_vector = embedding_model.encode([clean_text])
    probs      = ml_model.predict_proba(log_vector)[0]

    label_id   = probs.argmax()
    confidence = float(probs[label_id])
    label      = label_encoder.inverse_transform([label_id])[0]

    return {
        "clean_text":    clean_text,            # ← written to state for llm_node
        "log_vector":    log_vector[0].tolist(),
        "ml_label":      label,
        "ml_confidence": confidence,
        # Don't stamp final_source here — router decides if ML is confident enough
    }