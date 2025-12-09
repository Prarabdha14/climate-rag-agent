# scripts/fill_text_from_pdfs.py
"""
For each .txt in data/text:
 - if file is empty, try to find a PDF with a matching basename in data/pdfs or common alternate folders
 - extract text using pdfminer and save into the .txt file
"""
from pathlib import Path
from pdfminer.high_level import extract_text

TEXT_DIR = Path("data/text")
PDF_DIRS = [Path("data/pdfs"), Path("data/pdf"), Path("Data/pdf"), Path("Data/pdfs")]

def find_pdf_for_txt(txt_path: Path):
    name = txt_path.stem  # e.g., climate_basics
    for d in PDF_DIRS:
        if not d.exists():
            continue
        for p in d.glob("*.pdf"):
            if name.lower() in p.stem.lower():
                return p
    return None

def main():
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    for txt in TEXT_DIR.glob("*.txt"):
        size = txt.stat().st_size
        if size > 20:
            print(f"SKIP (non-empty): {txt} ({size} bytes)")
            continue
        print(f"FILLING: {txt} (empty, trying to find matching PDF...)")
        pdf = find_pdf_for_txt(txt)
        if not pdf:
            print("  No matching PDF found for", txt.name)
            continue
        try:
            text = extract_text(str(pdf))
            if not text or len(text.strip()) < 10:
                print("  PDF text extraction produced empty text for", pdf.name)
                continue
            txt.write_text(text, encoding="utf-8")
            print("  WROTE text from", pdf.name, "->", txt.name)
        except Exception as e:
            print("  ERROR extracting from", pdf, e)

if __name__ == "__main__":
    main()
