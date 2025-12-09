# src/core/ocr_processor.py
from pathlib import Path
try:
    from PIL import Image
    import pytesseract
    # FIX: Allow loading large scientific images (bypass decompression bomb check)
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
        """
        Extract text from an image or scanned PDF using Tesseract.
        """
        if not pytesseract or not Image:
            print("[WARN] Tesseract/Pillow not installed. OCR skipped.")
            return ""

        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        text = ""

        try:
            # 1. Handle PDFs (Scanned Documents)
            if suffix == ".pdf":
                if not convert_from_path:
                    print("[WARN] pdf2image not installed. Cannot OCR PDF.")
                    return ""
                
                # Convert PDF pages to images
                images = convert_from_path(str(file_path))
                for image in images:
                    text += pytesseract.image_to_string(image) + "\n\n"

            # 2. Handle Images (JPG, PNG, etc.)
            else:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)

        except Exception as e:
            print(f"[OCR ERROR] {file_path.name}: {e}")
            return ""

        return text