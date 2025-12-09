# src/main.py
import argparse
from pathlib import Path
from core.orchestrator import PipelineOrchestrator

def collect_demo_files():
    root = Path("data")
    files = []

    # PDFs
    files.extend((root / "pdfs").glob("*.pdf"))

    # Text
    files.extend((root / "text").glob("*.txt"))

    # Images
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        files.extend((root / "images").glob(ext))

    # Audio
    for ext in ["*.wav", "*.mp3"]:
        files.extend((root / "audio").glob(ext))

    # YouTube transcripts (.txt after your conversion step)
    files.extend((root / "youtube_transcripts").glob("*.txt"))

    return files

def demo_run(no_llm: bool):
    orchestrator = PipelineOrchestrator(use_llm=not no_llm)

    files = collect_demo_files()
    if not files:
        print("No sample files found in data/. Place sample files and rerun with --demo.")
        return 0

    outputs = []
    for s in files:
        s = Path(s)
        suf = s.suffix.lower()

        if suf == ".pdf":
            outputs.append(orchestrator.process_pdf(s))
        elif suf == ".txt":
            outputs.append(orchestrator.process_text(s))
        elif suf in [".jpg", ".jpeg", ".png", ".webp"]:
            outputs.append(orchestrator.process_image(s))
        elif suf in [".wav", ".mp3"]:
            outputs.append(orchestrator.process_audio(s))

    for o in outputs:
        print("=" * 80)
        print(f"FILE: {o.get('file')}")
        summaries = o.get("summaries", {})
        print("\nONE-LINE:\n", summaries.get("one_line", ""))
        print("\nTHREE-BULLETS:\n", summaries.get("three_bullets", ""))
        print("\nFIVE-SENTENCE:\n", summaries.get("five_sentence", ""))
        print("\nFOLLOW-UP NEEDED:", o.get("follow_up_needed", False))
        print("\nPROCESS LOGS:")
        for l in o.get("processing_log", []):
            print(" -", l)

    print("\nDemo complete.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Climate RAG demo runner")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample files")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM use")
    args = parser.parse_args()

    if args.demo:
        return demo_run(no_llm=args.no_llm)

    print("Run with --demo to execute deterministic demo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())