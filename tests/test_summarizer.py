# tests/test_summarizer.py
from core.summarizer import ExtractiveSummarizer

def test_summarizer_short_text():
    text = "Climate change increases global temperatures. Sea levels rise. Wildfires become more common."
    s = ExtractiveSummarizer()
    out = s.summarize_all(text)
    assert out["one_line"] != ""
    assert "three_bullets" in out
    assert "five_sentence" in out