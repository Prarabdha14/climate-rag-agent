# src/scripts/build_index.py
"""
Build retrieval index from text files in data/.
Produces:
 - data/index/index_meta.json
 - (TF-IDF) pickled vectorizer and matrix, OR
 - (FAISS) saved faiss index + embeddings if sentence-transformers available
"""
import json
from pathlib import Path
from core.utils import chunk_text, clean_text
import pickle
import numpy as np

ROOT = Path.cwd()
DATA_TEXT = ROOT / "data" / "text"
DATA_PDFS = ROOT / "data" / "pdfs"
OUT = ROOT / "data" / "index"
OUT.mkdir(parents=True, exist_ok=True)

def load_text_files():
    docs = []
    # text folder
    for p in sorted(DATA_TEXT.glob("*.txt")):
        txt = p.read_text(encoding="utf-8")
        docs.append({"id": str(p.name), "text": clean_text(txt), "source": str(p)})
    # try extracting simple text from PDFs using pdfminer
    from pdfminer.high_level import extract_text
    for p in sorted(DATA_PDFS.glob("*.pdf")):
        try:
            txt = extract_text(str(p))
            docs.append({"id": str(p.name), "text": clean_text(txt), "source": str(p)})
        except Exception as e:
            print("pdf text extract failed for", p, e)
    return docs

def chunk_docs(docs, chunk_size=500, overlap=100):
    chunks = []
    for d in docs:
        pieces = chunk_text(d["text"], chunk_size=chunk_size, overlap=overlap)
        for i, piece in enumerate(pieces):
            chunks.append({"id": f"{d['id']}_chunk{i}", "text": piece, "source": d["source"]})
    return chunks

def build_tfidf_index(chunks, outdir: Path):
    from sklearn.feature_extraction.text import TfidfVectorizer
    texts = [c["text"] for c in chunks]
    vec = TfidfVectorizer(stop_words="english")
    mat = vec.fit_transform(texts)
    # save
    pickle.dump(vec, open(outdir / "tfidf_vectorizer.pkl", "wb"))
    pickle.dump(mat, open(outdir / "tfidf_matrix.pkl", "wb"))
    open(outdir / "chunks_meta.json", "w", encoding="utf-8").write(json.dumps(chunks, indent=2))
    print("Saved TF-IDF index in", outdir)

def try_build_faiss(chunks, outdir: Path):
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
    except Exception as e:
        print("FAISS or sentence-transformers not available:", e)
        return False
    texts = [c["text"] for c in chunks]
    model = SentenceTransformer("all-MiniLM-L6-v2")
    emb = np.vstack([model.encode(t) for t in texts]).astype("float32")
    # build flat index
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(emb)
    index.add(emb)
    faiss.write_index(index, str(outdir / "faiss.index"))
    np.save(outdir / "embeddings.npy", emb)
    open(outdir / "chunks_meta.json", "w", encoding="utf-8").write(json.dumps(chunks, indent=2))
    print("Saved FAISS index in", outdir)
    return True

def main():
    docs = load_text_files()
    if not docs:
        print("No documents found in data/text or data/pdfs. Run the data downloader first.")
        return
    chunks = chunk_docs(docs)
    print(f"Created {len(chunks)} chunks.")
    # try FAISS first
    ok = try_build_faiss(chunks, OUT)
    if not ok:
        build_tfidf_index(chunks, OUT)
    print("Index build complete.")

if __name__ == "__main__":
    main()