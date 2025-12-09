# src/core/retrieval.py
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except Exception:
    ST_AVAILABLE = False

class Retriever:
    def __init__(self, docs: list, use_faiss: bool = False):
        """
        docs: list of dicts with keys: id, text, metadata
        """
        self.docs = docs
        self.texts = [d["text"] for d in docs]
        self.ids = [d["id"] for d in docs]
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.tfidf = None
        self.tfidf_matrix = None
        self.embed_model = None
        self.embeddings = None
        if self.use_faiss:
            if ST_AVAILABLE:
                self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.embeddings = np.vstack([self.embed_model.encode(t) for t in self.texts]).astype("float32")
                dim = self.embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dim)
                faiss.normalize_L2(self.embeddings)
                self.index.add(self.embeddings)
            else:
                # cannot use faiss without sentence-transformers; fallback to TF-IDF
                self.use_faiss = False
                self._fit_tfidf()
        else:
            self._fit_tfidf()

    def _fit_tfidf(self):
        self.tfidf = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.tfidf.fit_transform(self.texts)

    def retrieve(self, query: str, top_k: int = 5):
        if self.use_faiss and self.embed_model:
            q_emb = self.embed_model.encode([query]).astype("float32")
            faiss.normalize_L2(q_emb)
            D, I = self.index.search(q_emb, top_k)
            results = []
            for idx in I[0]:
                results.append(self.docs[idx])
            return results
        else:
            qv = self.tfidf.transform([query])
            sims = cosine_similarity(qv, self.tfidf_matrix)[0]
            top_idx = sims.argsort()[::-1][:top_k]
            return [self.docs[i] for i in top_idx]