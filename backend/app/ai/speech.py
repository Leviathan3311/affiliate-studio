"""Vietnamese voiceover: one WAV per shot.

VieNeu-TTS (voice Mỹ Duyên) on Modal CPU first; Gemini TTS (Interactions API, 24 kHz) when Modal
is not configured or fails, so a voice outage never blocks a video.

The video model only makes sound effects; its Vietnamese speech is not usable, so the spoken line
of each shot is synthesised here and mixed in by the notebook.
"""

import base64
import io
import logging
import wave

import httpx

from app.ai.llm import LLMUnavailable
from app.core.config import get_settings

URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
log = logging.getLogger(__name__)


def speak(text: str) -> bytes:
    s = get_settings()
    if s.tts_engine == "vieneu" and s.modal_app:
        try:
            return _vieneu(text)
        except Exception as e:  # noqa: BLE001 — any Modal failure falls back to Gemini
            log.warning("vieneu tts failed, using gemini: %s", type(e).__name__)
    return _gemini(text)


def _vieneu(text: str) -> bytes:
    import modal

    s = get_settings()
    voice = modal.Cls.from_name(s.modal_app, "Voice")()
    return voice.speak.remote(text, s.tts_voice, s.tts_temperature)


def _gemini(text: str) -> bytes:
    s = get_settings()
    if not s.gemini_api_key:
        raise LLMUnavailable("no api key")
    errors = []
    for model in s.gemini_tts_models:
        body = {
            "model": model,
            "input": [
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                            "annotations": [
                                {"type": "speech_metadata", "style": s.gemini_tts_style}
                            ],
                        }
                    ],
                }
            ],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": s.gemini_tts_voice}]},
        }
        try:
            r = httpx.post(
                URL, headers={"x-goog-api-key": s.gemini_api_key}, json=body, timeout=120
            )
            r.raise_for_status()
            audio = [
                c
                for step in r.json()["steps"]
                if step["type"] == "model_output"
                for c in step["content"]
                if c["type"] == "audio"
            ][-1]
            return base64.b64decode(audio["data"])
        except httpx.HTTPStatusError as e:
            errors.append(f"{model}: HTTP {e.response.status_code}")
        except (httpx.TransportError, KeyError, IndexError, ValueError) as e:
            errors.append(f"{model}: {type(e).__name__}")
    raise LLMUnavailable("tts: " + "; ".join(errors))


def seconds(wav: bytes) -> float:
    with wave.open(io.BytesIO(wav)) as w:
        return w.getnframes() / w.getframerate()
