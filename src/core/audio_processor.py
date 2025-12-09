# src/core/audio_processor.py
import json
import os
import wave
import subprocess
from pathlib import Path

class AudioUnavailable(Exception):
    pass

class AudioProcessor:
    def __init__(self, model_path="models/vosk-model-small"):
        self.model_path = model_path
        self.model = None

    def _ensure_model(self):
        if self.model is not None:
            return
        try:
            from vosk import Model
        except ImportError:
            raise AudioUnavailable(
                "VOSK library not found. Run: pip install vosk"
            )
        
        if not os.path.exists(self.model_path):
            raise AudioUnavailable(
                f"Vosk model not found at '{self.model_path}'. "
                "Please download it from https://alphacephei.com/vosk/models and unpack it there."
            )
            
        try:
            self.model = Model(self.model_path)
        except Exception as e:
            raise AudioUnavailable(f"Failed to load VOSK model: {e}")

    def transcribe(self, path: Path) -> str:
        """
        Transcribe audio using VOSK.
        Uses system FFmpeg directly to convert MP3/M4A to 16kHz WAV (bypassing pydub).
        """
        self._ensure_model()
        from vosk import KaldiRecognizer

        # Temporary file for the converted WAV
        temp_wav = path.with_suffix(".tmp.wav")

        try:
            # 1. Direct FFmpeg Conversion
            # Command: ffmpeg -i input.mp3 -ac 1 -ar 16000 -f wav output.wav -y
            cmd = [
                "ffmpeg",
                "-i", str(path),      # Input file
                "-ac", "1",           # Mono channel (required for VOSK)
                "-ar", "16000",       # 16000 Hz sample rate (required for VOSK)
                "-f", "wav",          # Format
                str(temp_wav),        # Output file
                "-y",                 # Overwrite if exists
                "-v", "quiet"         # Suppress logs
            ]
            
            # Run the command
            subprocess.run(cmd, check=True)
            
            # 2. Open the clean WAV file
            wf = wave.open(str(temp_wav), "rb")
            
        except subprocess.CalledProcessError:
            raise AudioUnavailable(f"Failed to convert audio file: {path}. Is it corrupted?")
        except FileNotFoundError:
            raise AudioUnavailable("FFmpeg not found. Please run: brew install ffmpeg")
        except Exception as e:
            raise AudioUnavailable(f"Audio processing error: {e}")

        # 3. Run Transcription
        try:
            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)
            
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part = json.loads(rec.Result())
                    results.append(part.get("text", ""))
            
            final_part = json.loads(rec.FinalResult())
            results.append(final_part.get("text", ""))
            
        finally:
            wf.close()
            # Clean up the temp file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

        return " ".join([r for r in results if r])