import os
import sys
import shutil

print("--- CLIMATE RAG SYSTEM CHECK ---")

# 1. Check Model
model_path = "models/vosk-model-small"
if os.path.exists(model_path) and os.path.isdir(model_path):
    print(f"✅ Model found: {model_path}")
else:
    print(f"❌ Model MISSING. Expected folder at: {model_path}")

# 2. Check Python Libraries
try:
    import vosk
    print("✅ Vosk Library: Installed")
except ImportError:
    print("❌ Vosk Library: MISSING (Run: pip install vosk)")

try:
    import pdf2image
    print("✅ pdf2image Library: Installed")
except ImportError:
    print("❌ pdf2image Library: MISSING (Run: pip install pdf2image)")

# 3. Check System Tools
if shutil.which("pdftoppm"): # Part of poppler
    print("✅ Poppler (PDF Tool): Installed")
else:
    print("❌ Poppler (PDF Tool): MISSING (Run: brew install poppler)")

if shutil.which("ffmpeg"):
    print("✅ FFmpeg (Audio Tool): Installed")
else:
    print("❌ FFmpeg (Audio Tool): MISSING (Run: brew install ffmpeg)")

print("--------------------------------")