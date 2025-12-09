# src/scripts/query_test.py

import json
from pathlib import Path
import numpy as np

INDEX_DIR = Path("data/index")
CHUNKS_META = INDEX_DIR / "chunks_meta.json"
FAISS_INDEX = INDEX_DIR / "faiss.index"
EMBEDDINGS = INDEX_DIR / "embeddings.npy"


def load_chunks():
    return json.load(open(CHUNKS_META, encoding="utf-8"))


def query_faiss(query_text, topk=5):
    """
    Query FAISS index if available.
    """
    import faiss
    from sentence_transformers import SentenceTransformer

    # Load model
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Load index & embeddings
    index = faiss.read_index(str(FAISS_INDEX))
    chunk_meta = load_chunks()

    # Encode query
    q_emb = model.encode([query_text]).astype("float32")

    # Search
    scores, idx = index.search(q_emb, topk)

    print("\n=== FAISS RESULTS ===")
    for score, i in zip(scores[0], idx[0]):
        chunk = chunk_meta[i]
        print(
            f"\n--- {chunk['id']} (source: {chunk['source']}) score={score:.4f}\n"
            f"{chunk['text'][:300]}...\n"
        )


def query_tfidf(query_text, topk=5):
    """
    Fallback if FAISS index does not exist.
    """
    import pickle
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = pickle.load(open(INDEX_DIR / "tfidf_vectorizer.pkl", "rb"))
    matrix = pickle.load(open(INDEX_DIR / "tfidf_matrix.pkl", "rb"))
    chunks = load_chunks()

    q_vec = vectorizer.transform([query_text])
    sims = cosine_similarity(q_vec, matrix)[0]

    top_idx = np.argsort(sims)[::-1][:topk]

    print("\n=== TF-IDF RESULTS ===")
    for i in top_idx:
        chunk = chunks[i]
        print(
            f"\n--- {chunk['id']} (source: {chunk['source']}) score={sims[i]:.4f}\n"
            f"{chunk['text'][:300]}...\n"
        )


if __name__ == "__main__":
    query = "sea level rise and ocean warming impacts"

    print(f"\nRunning query: {query}\n")

    if FAISS_INDEX.exists():
        query_faiss(query)
    else:
        query_tfidf(query)