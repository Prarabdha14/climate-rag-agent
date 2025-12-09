# scripts/generate_sample_data.py
"""
Sample data downloader scaffold.

Usage:
  1. Edit `scripts/urls_to_download.json` with actual URLs you want to download (see example).
  2. Run: python scripts/generate_sample_data.py
This script will download PDFs, HTML articles (saved as .txt), images, audio,
and try to fetch YouTube transcripts (if available) into the data/ folder.
"""
import os
import json
from pathlib import Path
import requests
from urllib.parse import urlparse
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

ROOT = Path.cwd()
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
(DATAPDF := DATA / "pdfs").mkdir(exist_ok=True)
(DATATXT := DATA / "text").mkdir(exist_ok=True)
(DATAIMG := DATA / "images").mkdir(exist_ok=True)
(DATAAUDIO := DATA / "audio").mkdir(exist_ok=True)
(DATAYT := DATA / "youtube_transcripts").mkdir(exist_ok=True)

# Example file to edit with your target URLs
URL_FILE = Path("scripts/urls_to_download.json")

EXAMPLE = {
  "pdfs": [
    # Replace with direct PDF links
    "https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_SPM.pdf"
  ],
  "text": [
    # article URLs (will fetch and save as .txt by stripping HTML tags simply)
    "https://www.nationalgeographic.com/environment/article/climate-change-overview"
  ],
  "images": [
    # direct image links
    "https://climate.nasa.gov/system/downloadable_items/970_Global_Temperatures-2020-2021.png"
  ],
  "audio": [
    # direct mp3 URLs if available
  ],
  "youtube": [
    # YouTube video IDs (not full URLs) - e.g., "dQw4w9WgXcQ"
  ]
}

def load_urls():
    if not URL_FILE.exists():
        print("Creating example", URL_FILE)
        URL_FILE.write_text(json.dumps(EXAMPLE, indent=2))
        print("Edit the JSON file with the actual URLs / YouTube IDs you want, then re-run this script.")
        raise SystemExit(1)
    data = json.loads(URL_FILE.read_text(encoding="utf-8"))
    return data

def download_file(url, dest: Path, headers=None):
    try:
        r = requests.get(url, stream=True, timeout=30, headers=headers)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Saved:", dest)
        return True
    except Exception as e:
        print("Download failed:", url, e)
        return False

def save_text_from_html(url, dest: Path):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        # Very simple HTML -> plain text cleaning (strip tags)
        text = r.text
        import re
        text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.S)
        text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.S)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()
        dest.write_text(text, encoding="utf-8")
        print("Saved article text:", dest)
        return True
    except Exception as e:
        print("Failed to fetch article:", url, e)
        return False

def download_youtube_transcript(video_id, dest: Path):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        dest.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        print("Saved YouTube transcript:", dest)
        return True
    except NoTranscriptFound:
        print("No transcript for", video_id)
        return False
    except Exception as e:
        print("YT transcript failed:", video_id, e)
        return False

def main():
    urls = load_urls()
    # PDFs
    for url in urls.get("pdfs", []):
        parsed = urlparse(url)
        name = Path(parsed.path).name or "download.pdf"
        dest = DATAPDF / name
        download_file(url, dest)

    # Articles -> txt
    for url in urls.get("text", []):
        parsed = urlparse(url)
        name = Path(parsed.path).name or "article"
        if not name.endswith(".txt"):
            name = name + ".txt"
        dest = DATATXT / name
        save_text_from_html(url, dest)

    # Images
    for url in urls.get("images", []):
        parsed = urlparse(url)
        name = Path(parsed.path).name or "image"
        dest = DATAIMG / name
        download_file(url, dest)

    # Audio
    for url in urls.get("audio", []):
        parsed = urlparse(url)
        name = Path(parsed.path).name or "audio"
        dest = DATAAUDIO / name
        download_file(url, dest)

    # YouTube transcripts (video IDs)
    for vid in urls.get("youtube", []):
        dest = DATAYT / (vid + "_transcript.json")
        download_youtube_transcript(vid, dest)

    print("Download stage complete. Check data/ folder.")

if __name__ == "__main__":
    main()