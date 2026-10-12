"""
Audio Speech Generation Service
Uses gTTS (Google Text-to-Speech) to generate audio explanations in Marathi, Hindi, and English.
Caches generated MP3 files in app/static/audio/ to avoid repeated API requests.
"""

import hashlib
from pathlib import Path
from gtts import gTTS

AUDIO_DIR = Path(__file__).resolve().parent.parent / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Map our app language codes to gTTS language codes
LANG_CODE_MAP = {
    "mr": "mr",    # Marathi
    "hi": "hi",    # Hindi
    "en": "en"     # English
}

def generate_treatment_audio(text: str, lang: str = "mr") -> str | None:
    """
    Generates an MP3 file from text in Marathi, Hindi, or English.
    Returns the relative web URL of the audio file (e.g., /static/audio/abc123.mp3).
    """
    if not text or len(text.strip()) == 0:
        return None

    try:
        # Create unique filename based on MD5 hash of text and language
        text_hash = hashlib.md5(f"{lang}_{text}".encode("utf-8")).hexdigest()
        filename = f"{text_hash}.mp3"
        filepath = AUDIO_DIR / filename

        # Return cached file if already generated
        if filepath.exists():
            return f"/static/audio/{filename}"

        # Generate audio using gTTS
        gtts_lang = LANG_CODE_MAP.get(lang, "en")
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(str(filepath))

        return f"/static/audio/{filename}"

    except Exception as e:
        print(f"[!] Warning: Audio synthesis skipped ({e})")
        return None
