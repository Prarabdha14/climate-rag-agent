# Use a lightweight Python base image
FROM python:3.10-slim

# 1. Install System Dependencies (FFmpeg for Audio, Tesseract for OCR)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    tesseract-ocr \
    poppler-utils \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# 2. Copy Requirements and Install Python Deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Download the Vosk Model (So we don't need to upload it to Git)
# This keeps your repo light but ensures the model exists on the server
RUN mkdir -p models && \
    wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip vosk-model-small-en-us-0.15.zip && \
    mv vosk-model-small-en-us-0.15 models/vosk-model-small && \
    rm vosk-model-small-en-us-0.15.zip

# 4. Copy Your Application Code
COPY src/ src/
COPY Data/ data/

# Create necessary folders for temp storage
RUN mkdir -p demo/outputs uploads

# 5. Command to start the server (Render sets the PORT environment variable)
CMD ["sh", "-c", "uvicorn src.api.app:app --host 0.0.0.0 --port $PORT"]