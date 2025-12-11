# src/core/orchestrator.py
from pathlib import Path
from typing import Optional
import json
import math
from difflib import SequenceMatcher
import re

from .summarizer import ExtractiveSummarizer
from .ocr_processor import OCRProcessor
from .audio_processor import AudioProcessor, AudioUnavailable
from .utils import clean_text, clean_transcript_text, save_output_json, log_processing
from core.storage import init_db, record_upload, record_result

# Try importing Sentiment Analyzer (Optional)
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
except Exception:
    SentimentIntensityAnalyzer = None

# Initialize DB on import
try:
    init_db()
except Exception as e:
    print("Warning: init_db() failed:", e)

# --- Helper Functions ---
def _near_duplicate(a: str, b: str, thresh: float = 0.86) -> bool:
    if not a or not b: return False
    a_n = re.sub(r"\s+", " ", a.strip().lower())
    b_n = re.sub(r"\s+", " ", b.strip().lower())
    sm = SequenceMatcher(None, a_n, b_n)
    return sm.quick_ratio() >= thresh or sm.ratio() >= thresh

def _cleanup_summary_field(text: str, max_chars: int = 400) -> str:
    if not text: return ""
    text = text.replace("%", " ")
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    parts = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    cleaned = []
    for p in parts:
        if cleaned and _near_duplicate(p, cleaned[-1]): continue
        cleaned.append(p)
    out = " ".join(cleaned)
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "..."
    return out.strip()

# --- COST ESTIMATION LOGIC ---
def _calculate_cost(text: str = "", image_count: int = 0, audio_seconds: int = 0) -> dict:
    word_count = len(text.split()) if text else 0
    est_tokens = int(word_count * 1.33)
    text_cost = (est_tokens / 1_000_000) * 0.15
    image_cost = image_count * 0.002
    audio_cost = (audio_seconds / 60) * 0.006
    total_usd = text_cost + image_cost + audio_cost
    
    return {
        "tokens": est_tokens,
        "estimated_cost_usd": round(total_usd, 6),
        "details": f"{est_tokens} tokens, {image_count} images, {audio_seconds}s audio"
    }

class PipelineOrchestrator:
    def __init__(self, use_llm: bool = False):
        self.summarizer = ExtractiveSummarizer()
        self.ocr = OCRProcessor()
        self.audio = None
        self.use_llm = use_llm
        try:
            self.sentiment = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else None
        except Exception:
            self.sentiment = None

    def process_pdf(self, path: Path):
        path = Path(path)
        method = "text-extraction"
        text = self._extract_pdf_text(path)
        if not text or len(text.strip()) < 300:
            method = "ocr"
            text = self.ocr.ocr_file(path)
        text = clean_text(text)
        cost_info = _calculate_cost(text=text)
        return self._postprocess_and_save(path, text, method, cost_info)

    def process_text(self, path: Path):
        path = Path(path)
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() in (".vtt", ".srt"):
            text = clean_transcript_text(raw)
        else:
            text = clean_text(raw)
        cost_info = _calculate_cost(text=text)
        return self._postprocess_and_save(path, text, "text", cost_info)

    def process_image(self, path: Path):
        path = Path(path)
        text = clean_text(self.ocr.ocr_file(path))
        cost_info = _calculate_cost(text=text, image_count=1)
        return self._postprocess_and_save(path, text, "image_ocr", cost_info)

    def process_audio(self, path: Path):
        path = Path(path)
        if not self.audio:
            self.audio = AudioProcessor()
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        est_seconds = int(file_size_mb * 60) # Rough estimate
        
        try:
            transcript = self.audio.transcribe(path)
        except AudioUnavailable as e:
            print(f"[WARN] Audio unavailable: {e}")
            return self._postprocess_and_save(path, "", "audio_transcript")
        except Exception as e:
            print(f"[WARN] Audio failed: {e}")
            return self._postprocess_and_save(path, "", "audio_transcript")
            
        transcript = clean_text(transcript)
        cost_info = _calculate_cost(text=transcript, audio_seconds=est_seconds)
        return self._postprocess_and_save(path, transcript, "audio_transcript", cost_info)

    def _extract_pdf_text(self, path: Path) -> Optional[str]:
        try:
            from pdfminer.high_level import extract_text
            return extract_text(str(path))
        except Exception:
            return None

    def _postprocess_and_save(self, path: Path, text: str, method: str, cost_info: dict = None):
        if cost_info is None:
            cost_info = {"tokens": 0, "estimated_cost_usd": 0.0}

        out = {
            "file": str(path), 
            "method": method, 
            "processing_log": [],
            "cost_analysis": cost_info
        }
        
        out["processing_log"].append(f"method={method}")
        out["processing_log"].append(f"cost_est=${cost_info['estimated_cost_usd']}")

        if not text or len(text.strip()) < 20:
            out["summaries"] = {"one_line": "", "three_bullets": "", "five_sentence": ""}
            out["follow_up_needed"] = True
            save_output_json(out)
            return out

        summaries = self.summarizer.summarize_all(text)
        
        # Cleanup summary text
        try:
            for k in ["one_line", "three_bullets", "five_sentence"]:
                if k in summaries:
                    summaries[k] = _cleanup_summary_field(summaries[k])
        except Exception:
            pass

        out["summaries"] = summaries

        # Sentiment
        if self.sentiment:
            try:
                vs = self.sentiment.polarity_scores(text)
                label = "neutral"
                if vs["compound"] >= 0.05: label = "positive"
                elif vs["compound"] <= -0.05: label = "negative"
                out["sentiment"] = {"label": label, "score": vs["compound"]}
            except Exception:
                out["sentiment"] = {"label": "unknown", "score": 0.0}
        else:
            out["sentiment"] = {"label": "unknown", "score": 0.0}

        out["follow_up_needed"] = False
        save_output_json(out)
        log_processing(f"{path} processed successfully via {method}")
        
        # Save to DB
        try:
            filename = path.name
            filepath = str(path.resolve())
            filetype = Path(filename).suffix.lstrip(".").lower()
            upload_id = record_upload(filename, filepath, filetype=filetype, source="local")
            record_result(upload_id, str(Path("demo/outputs") / f"{path.stem}_summary.json"), summaries, out.get("sentiment"), out["follow_up_needed"])
        except Exception as e:
            print("Warning: failed to write DB:", e)

        return out