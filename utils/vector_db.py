import faiss
import numpy as np

class VectorDB:
    def __init__(self, dim):
        self.index = faiss.IndexFlatIP(dim) # cosine similarity 
        self.texts = [] 
        self.labels = []

    def _normalize(self, vec): 
        norm = np.linalg.norm(vec) 
        return vec / (norm + 1e-10)
    
    def insert(self, text, embedding, label):
        vec = np.array(embedding).astype("float32")
        vec = self._normalize(vec) 
        self.index.add(np.array([vec]))
        self.texts.append(text)
        self.labels.append(label)

    def search(self, embedding, top_k=5):

        if self.index.ntotal == 0: 
            return None

        vec = np.array(embedding).astype("float32")
        vec = self._normalize(vec) 

        scores, indices = self.index.search(np.array([vec]), top_k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1: 
                continue

            results.append({
                    "text": self.texts[idx],
                    "label": self.labels[idx],
                    "score": float(score)
                })
        return results