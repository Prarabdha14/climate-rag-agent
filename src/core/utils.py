# src/core/utils.py
import re
import json
from pathlib import Path
from typing import List
from difflib import SequenceMatcher

# -------------------------
# low-level helpers
# -------------------------
def _strip_inline_tokens(line: str) -> str:
    line = re.sub(r"\balign:\S+\b", "", line)
    line = re.sub(r"\bposition:\S+\b", "", line)
    line = re.sub(r"\bstart:\d+%?\b", "", line)
    line = line.replace("%", " ")
    line = re.sub(r"[ \t]{2,}", " ", line)
    return line.strip()

def _near_duplicate(a: str, b: str, thresh: float = 0.86) -> bool:
    if not a or not b:
        return False
    a_n = re.sub(r"\s+", " ", a.strip().lower())
    b_n = re.sub(r"\s+", " ", b.strip().lower())
    sm = SequenceMatcher(None, a_n, b_n)
    return sm.quick_ratio() >= thresh or sm.ratio() >= thresh

def _dedupe_adjacent_paragraphs(paragraphs: List[str]) -> List[str]:
    out = []
    for p in paragraphs:
        if not p:
            continue
        if out and (_near_duplicate(p, out[-1]) or p.strip() == out[-1].strip()):
            continue
        out.append(p)
    return out

def _dedupe_adjacent_sentences(text: str) -> str:
    pieces = re.split(r'(?<=[\.\?\!])\s+', text)
    cleaned = []
    for s in pieces:
        s = s.strip()
        if not s:
            continue
        s = _strip_inline_tokens(s)
        if cleaned and _near_duplicate(s, cleaned[-1]):
            continue
        cleaned.append(s)
    return " ".join(cleaned)

def _collapse_exact_repeats(text: str) -> str:
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    out = []
    i = 0
    n = len(paras)
    while i < n:
        j = i + 1
        while j < n and paras[j] == paras[i]:
            j += 1
        out.append(paras[i])
        i = j
    return "\n\n".join(out)

def _collapse_repeated_sequence(text: str) -> str:
    pattern = re.compile(r'(\b[\w,;:\'"\-\—\(\) ]{10,200}?\b)(\s+\1){1,}', flags=re.I)
    prev = None
    out = text
    while prev != out:
        prev = out
        out = pattern.sub(r'\1', out)
    return out

# -------------------------
# main transcript cleaner
# -------------------------
def clean_transcript_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # remove WEBVTT header and common metadata blocks
    text = re.sub(r"(?im)^\s*WEBVTT.*?\n", "", text, count=1)
    text = re.sub(r"(?m)^(NOTE|STYLE|REGION|X-TIMESTAMP-MAP):.*\n", "", text)

    # remove Kind/Language header lines
    text = re.sub(r"(?im)^\s*(Kind|Language)\s*:\s*.*\n", "", text)

    # remove arrow timestamp lines
    text = re.sub(r"(?m)^\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?\s*-->\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?.*\n", "", text)

    # remove cue number lines
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    # remove inline timestamp tokens like <00:00:05.000>
    text = re.sub(r"<\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?>", " ", text)
    text = re.sub(r"<\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?[^>]*>", " ", text)

    # remove bare timestamp fragments like 00:00:05.000 outside arrows
    text = re.sub(r"\b\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?\b", " ", text)

    # remove align/position tokens
    text = re.sub(r"align:\S+", " ", text)
    text = re.sub(r"position:\S+", " ", text)
    text = re.sub(r"start:\d+%?", " ", text)

    # remove <c> and <v> tags and broken variants
    text = re.sub(r"</?[cCvV][^>]*>", " ", text)
    text = re.sub(r"\b[cCvV]>\b", " ", text)
    text = re.sub(r"</[cCvV]>", " ", text)
    text = re.sub(r"\b/ ?c>\b", " ", text)

    # remove any other HTML-like tags
    text = re.sub(r"<[^>]+>", " ", text)

    # remove stage directions like [music], (applause), (laughter)
    text = re.sub(r"[\[\(]\s*(?:music|applause|laughter|noise|laughs?|sighs?|breath|cough)[\]\)]", " ", text, flags=re.I)

    # remove remaining bracketed/parenthetical pieces
    text = re.sub(r"\[.*?\]", " ", text)
    text = re.sub(r"\(.*?\)", " ", text)

    # collapse spaces/newlines
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # split into paragraphs and clean
    raw_paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    paras = []
    for para in raw_paras:
        lines = [ln.strip() for ln in para.splitlines() if ln.strip()]
        if not lines:
            continue
        joined = " ".join([_strip_inline_tokens(ln) for ln in lines])
        joined = re.sub(r"\s{2,}", " ", joined).strip()
        if not joined:
            continue
        joined = _dedupe_adjacent_sentences(joined)
        paras.append(joined)

    paras = _dedupe_adjacent_paragraphs(paras)

    cleaned = "\n\n".join(paras)
    cleaned = _collapse_exact_repeats(cleaned)
    cleaned = _collapse_repeated_sequence(cleaned)

    cleaned = re.sub(r"%+", " ", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()

# -------------------------
# public helpers used by the pipeline
# -------------------------
def clean_text(text: str) -> str:
    """
    Generic cleaning entry point used by orchestrator.

    If input looks like captions/subtitles (WEBVTT, timestamp tokens or <00:..> fragments),
    route to the stronger transcript cleaner. Otherwise do lightweight normalization.
    """
    if not text:
        return ""

    # quick heuristic: if it contains WEBVTT header or timestamp arrow or angle-bracket timestamps,
    # treat as transcript/captions and use the transcript cleaner
    if re.search(r"\bWEBVTT\b", text, re.I) or re.search(r"\d{1,2}:\d{2}:\d{2}\s*-->", text) or re.search(r"<\d{1,2}:\d{2}:\d{2}", text):
        return clean_transcript_text(text)

    # fallback: lightweight cleaning for normal text/html scrapings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
    if not text:
        return []
    approx_chunk_size = max_tokens * 4
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(L, start + approx_chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap * 4
        if start < 0:
            start = 0
        if start >= L:
            break
    return chunks

def save_output_json(obj: dict, out_dir: str = "demo/outputs") -> Path:
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    fname = obj.get("file", "output").replace("/", "_").replace("\\", "_")
    dest = outp / f"{Path(fname).stem}_summary.json"
    dest.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return dest

def log_processing(msg: str):
    print(msg)