# src/api/app.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional, Any, Dict
import json
import shutil
import traceback
import concurrent.futures
import functools
import contextlib
import sys

# --- IMPORTS ---
try:
    from core.orchestrator import PipelineOrchestrator
except ImportError:
    PipelineOrchestrator = None

try:
    from core.retrieval import Retriever
except ImportError:
    Retriever = None

# --- SAFETY CHUNKER (Prevents Hangs) ---
def simple_chunker(text, chunk_size=1000):
    """
    A dead-simple chunker that cannot freeze.
    It just slices string[0:1000], string[1000:2000], etc.
    """
    if not text:
        return []
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# --- GLOBALS ---
_retriever = None
_orchestrator = None

# --- LIFESPAN (Startup Logic) ---
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Orchestrator
    global _orchestrator
    try:
        print("⚡ [STARTUP] Initializing Orchestrator...", flush=True)
        _orchestrator = PipelineOrchestrator(use_llm=False)
        print("   ✅ Orchestrator Ready.", flush=True)
    except Exception as e:
        print(f"   ❌ [STARTUP] Orchestrator failed: {e}", flush=True)

    # 2. Initialize Retriever
    global _retriever
    try:
        print("⚡ [STARTUP] Building Search Index (Safe Mode)...", flush=True)
        docs = []
        txt_dir = Path.cwd() / "data" / "text"
        
        if txt_dir.exists():
            files = sorted(list(txt_dir.glob("*.txt")))
            print(f"   📂 Found {len(files)} text files.", flush=True)
            
            for fp in files:
                print(f"   👉 Indexing: {fp.name} ... ", end="", flush=True)
                try:
                    full_text = fp.read_text(encoding="utf-8", errors="ignore") # Ignore bad chars
                    if not full_text.strip(): 
                        print("Skipped (Empty)", flush=True)
                        continue
                    
                    # USE SIMPLE CHUNKER
                    chunks = simple_chunker(full_text)
                    
                    for i, chunk in enumerate(chunks):
                        docs.append({
                            "id": f"{fp.name}_part_{i+1}",
                            "text": chunk,
                            "source": str(fp.resolve())
                        })
                    print("OK", flush=True)
                    
                except Exception as e:
                    print(f"ERROR: {e}", flush=True)
        
        print(f"   🧠 Training Retriever with {len(docs)} chunks...", flush=True)
        
        if docs and Retriever:
            _retriever = Retriever(docs)
            # Attach search adapter
            if not hasattr(_retriever, "search"):
                if hasattr(_retriever, "retrieve"):
                    _retriever.search = lambda q, k=5: _retriever.retrieve(q, k)
                elif hasattr(_retriever, "query"):
                    _retriever.search = lambda q, k=5: _retriever.query(q, top_k=k)
                elif hasattr(_retriever, "tfidf"):
                    _retriever.search = lambda q, k=5: _retriever.tfidf(q, k)
            print(f"✅ [STARTUP] Index Ready.", flush=True)
        else:
            print("⚠️ [STARTUP] Index empty (this is fine, just means no search results yet).", flush=True)
            
    except Exception as e:
        print(f"❌ [STARTUP] Retriever failed: {e}", flush=True)
        traceback.print_exc()

    yield

# --- APP DEFINITION ---
app = FastAPI(title="Climate RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPERS ---
def safe_search_runner(retriever, query, k=5):
    if not retriever: return []
    try:
        return retriever.search(query, k)
    except Exception:
        return []

# --- ENDPOINTS ---
@app.get("/health")
def health():
    return {"status": "ok", "retriever": _retriever is not None}

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    if _orchestrator is None:
        raise HTTPException(500, "Orchestrator not initialized")
        
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest = uploads_dir / Path(file.filename).name
    
    with open(dest, "wb") as fh:
        shutil.copyfileobj(file.file, fh)

    try:
        suffix = dest.suffix.lower()
        if suffix == ".pdf": result = _orchestrator.process_pdf(dest)
        elif suffix == ".txt": result = _orchestrator.process_text(dest)
        elif suffix in [".jpg", ".png", ".jpeg", ".webp"]: result = _orchestrator.process_image(dest)
        elif suffix in [".wav", ".mp3", ".m4a"]: result = _orchestrator.process_audio(dest)
        else: result = _orchestrator.process_text(dest)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Processing error: {e}")

@app.post("/query")
def query(body: Dict[str, Any]):
    q = body.get("query", "")
    k = int(body.get("k", 5))
    
    if not q: return {"results": []}
    if _retriever is None: return {"results": [], "detail": "Index not ready."}

    try:
        raw_results = safe_search_runner(_retriever, q, k)
    except Exception as e:
        return {"results": [], "detail": str(e)}

    clean_results = []
    for r in raw_results:
        text_preview = r.get("text", "")
        if len(text_preview) > 300:
            text_preview = text_preview[:300] + "..."
            
        clean_results.append({
            "source": r.get("id", "unknown"),
            "content": text_preview,
            "score": float(r.get("score", 0.0)) if "score" in r else 0.0
        })

    return {"results": clean_results}

@app.get("/demo-outputs")
def demo_outputs():
    p = Path("demo/outputs")
    if not p.exists(): return {"outputs": []}
    files = sorted([str(fp) for fp in p.glob("*.json")])
    return {"outputs": files}