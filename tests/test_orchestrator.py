# tests/test_orchestrator.py
from core.orchestrator import PipelineOrchestrator
from pathlib import Path
import tempfile

def test_orchestrator_text(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Climate change causes sea level rise and temperature change.")
    orch = PipelineOrchestrator(use_llm=False)
    res = orch.process_text(p)
    assert "summaries" in res
    assert res["file"].endswith("sample.txt")