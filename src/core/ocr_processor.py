# src/core/ocr_processor.py
from pathlib import Path
try:
    from PIL import Image
    import pytesseract
    # Allow large images
    Image.MAX_IMAGE_PIXELS = None 
except ImportError:
    Image = None
    pytesseract = None

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

class OCRProcessor:
    def __init__(self):
        pass

    def ocr_file(self, file_path: Path) -> str:
        if not pytesseract or not Image:
            print("[WARN] Tesseract/Pillow not installed. OCR skipped.")
            return ""

        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        text = ""

        try:
            if suffix == ".pdf":
                if not convert_from_path:
                    return ""
                images = convert_from_path(str(file_path))
                for image in images:
                    text += pytesseract.image_to_string(image) + "\n\n"
            else:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
        except Exception as e:
            print(f"[OCR ERROR] {file_path.name}: {e}")
            return ""

        return text