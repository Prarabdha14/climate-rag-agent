# src/optional_llm/llm_client.py
import time
from pathlib import Path

class LLMClient:
    def __init__(self, api_key=None, log_path="logs/llm_runs.log"):
        self.api_key = api_key
        self.log_path = log_path
        Path("logs").mkdir(exist_ok=True, parents=True)

    def generate(self, prompt: str):
        ts = time.asctime()
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"{ts} | PROMPT: {prompt[:1000]}\n")
        # do not call remote LLM by default — placeholder behaviour
        return "[LLM output suppressed in default demo]"
