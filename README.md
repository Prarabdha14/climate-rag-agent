# 🌍 Climate RAG Agent

A multi-modal AI agent capable of ingesting **PDFs, Images, Audio, and Text** to answer climate-related queries. Built for the Datasmith AI assignment.

## 📹 Demo Video
[![Watch the Demo](https://img.youtube.com/vi/NoqMxjRmjy4/0.jpg)](https://youtu.be/NoqMxjRmjy4)

**[👉 Click Here to Watch the Demo Walkthrough](https://youtu.be/NoqMxjRmjy4)**

---

## ✨ Key Features
This agent meets all core requirements plus bonus objectives:

- **Multi-Modal Ingestion:**
  - 📄 **PDFs:** Hybrid extraction using `pdfminer` with `Tesseract OCR` fallback for scanned docs.
  - 🖼️ **Images:** Extracts text from scientific charts and infographics.
  - 🎙️ **Audio:** Offline speech-to-text using `Vosk` (Automatically converts MP3/M4A to WAV via FFmpeg).
  - 📺 **YouTube:** Fetches and cleans transcripts automatically.
- **💰 Cost Estimator (Bonus):** Calculates estimated token usage and USD cost for every file *before* processing (displayed in UI).
- **🧠 Agentic Workflow:** Detects ambiguous inputs (short text, empty summaries) and flags files requiring follow-up.
- **🔍 Semantic Search:** Chunked vector retrieval (TF-IDF/Cosine Similarity) for precise answers.
- **📊 Modern UI:** React-based dashboard with Glassmorphism design, Executive Summaries, and Detailed Logs.


Setup & Installation
1. Prerequisites
Python 3.10+ & Node.js

System Tools (Mac): brew install poppler ffmpeg tesseract

2. Backend Setup

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

mkdir models && cd models
curl -L -o vosk-model-small.zip "[https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip)"
unzip vosk-model-small.zip
mv vosk-model-small-en-us-0.15 vosk-model-small
cd ..

3. Frontend Setup
cd frontend
npm install

How to Run
1. Start the Backend API: # From root directory
source .venv/bin/activate
uvicorn src.api.app:app --reload

2. Start the User Interface: # From frontend directory
cd frontend
npm start

Testing
The project includes a pytest suite covering API endpoints, orchestrator logic, and summarization.
pytest

Project Structure
src/core/: Application logic (Orchestrator, Summarizer, Cost Logic).

src/api/: FastAPI routes and Search endpoints.

frontend/: React application.

data/: Storage for uploaded files and vector indices.

tests/: Automated test suite.

## 🛠️ System Architecture

The system uses a **Local-First** architecture to ensure privacy and zero recurring costs.

<br>

```mermaid
graph TD
    User[React UI] <-->|JSON| API[FastAPI]
    API --> Orchestrator[Orchestrator]
    
    Orchestrator -->|PDF| PDFProc[PDF Processor]
    Orchestrator -->|Audio| AudioProc[FFmpeg + Vosk]
    Orchestrator -->|Image| ImgProc[Tesseract OCR]
    
    subgraph "Core Logic"
        PDFProc & AudioProc & ImgProc --> Cleaner[Text Cleaner]
        Cleaner --> Cost[Cost Estimator]
        Cleaner --> Summarizer[Extractive Summarizer]
    end
    
    Summarizer --> DB[(SQLite / JSON)]
    Cleaner --> Index[Search Index]
