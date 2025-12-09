# src/core/summarizer.py
"""
Lightweight extractive summarizer using sentence tokenization + TF-IDF scoring.
Removes dependency on `sumy` so tests are simpler to run in constrained environments.
"""

from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk

# ensure punkt is available (download if missing)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

from nltk.tokenize import sent_tokenize

class ExtractiveSummarizer:
    def __init__(self):
        # We'll vectorize sentences with TF-IDF (unigram/bigram)
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2))

    def _split_sentences(self, text: str) -> List[str]:
        sents = [s.strip() for s in sent_tokenize(text) if s.strip()]
        return sents

    def _score_sentences(self, sentences: List[str]) -> List[float]:
        if not sentences:
            return []
        try:
            X = self.vectorizer.fit_transform(sentences)
            scores = X.sum(axis=1).A1  # sum of TF-IDF weights per sentence
            return scores.tolist()
        except Exception:
            # fallback: equal scores
            return [1.0 for _ in sentences]

    def summarize_all(self, text: str):
        if not text or len(text.strip()) == 0:
            return {"one_line": "", "three_bullets": "", "five_sentence": ""}

        sentences = self._split_sentences(text)
        if not sentences:
            return {"one_line": "", "three_bullets": "", "five_sentence": ""}

        scores = self._score_sentences(sentences)
        # pair sentences with scores and original index
        ranked = sorted(
            [(i, s, scores[i] if i < len(scores) else 0.0) for i, s in enumerate(sentences)],
            key=lambda x: x[2],
            reverse=True,
        )

        # pick top sentence for one-line (highest score)
        top1 = ranked[0][1] if ranked else ""

        # pick top 3 sentences preserving their order in original text
        top3_idx = sorted([r[0] for r in ranked[:3]]) if ranked else []
        top3 = " ".join([sentences[i] for i in top3_idx]) if top3_idx else ""

        # pick top 5 sentences preserving order
        top5_idx = sorted([r[0] for r in ranked[:5]]) if ranked else []
        top5 = " ".join([sentences[i] for i in top5_idx]) if top5_idx else ""

        return {"one_line": top1, "three_bullets": top3, "five_sentence": top5}
