import time
from typing import Callable, Optional

from app.models.credential import Credential
from app.models.results import (
    ConnectionResult, TextResult, ImageResult, AudioResult,
)
from .base import BaseProvider

_MOCK_MODELS = [
    {"technical_name": "mock-text-v1", "display_name": "Mock Text v1", "type": "text",
     "capabilities": ["chat", "streaming", "json_output", "tool_calling"]},
    {"technical_name": "mock-image-v1", "display_name": "Mock Image v1", "type": "image",
     "capabilities": ["image_gen"]},
    {"technical_name": "mock-audio-v1", "display_name": "Mock Audio v1", "type": "audio",
     "capabilities": ["transcription", "speech"]},
]

_MOCK_RESPONSES = {
    "mock-text-v1": "Ceci est une réponse simulée du provider Mock. Il ne fait aucun appel réseau.",
    "mock-image-v1": "https://via.placeholder.com/1024",
    "mock-audio-v1": "Transcription simulée : bonjour le monde.",
}


class MockProvider(BaseProvider):
    slug = "mock"

    def __init__(self, latency_ms: int = 200):
        self._latency_ms = latency_ms

    def _simulate_latency(self) -> None:
        time.sleep(self._latency_ms / 1000)

    def test_connection(self, credentials: Credential) -> ConnectionResult:
        self._simulate_latency()
        return ConnectionResult(success=True, message="Mock connection OK", latency_ms=self._latency_ms)

    def list_models(self, credentials: Credential) -> list:
        return list(_MOCK_MODELS)

    def run_text(self, credentials: Credential, model: str, params: dict,
                 on_chunk: Optional[Callable[[str], None]] = None) -> TextResult:
        self._simulate_latency()
        content = _MOCK_RESPONSES.get(model, "Réponse mock par défaut.")
        if on_chunk:
            for word in content.split():
                on_chunk(word + " ")
        return TextResult(
            success=True,
            content=content,
            model=model,
            prompt_tokens=10,
            completion_tokens=len(content.split()),
            total_tokens=10 + len(content.split()),
            latency_ms=self._latency_ms,
        )

    def run_image(self, credentials: Credential, model: str, params: dict) -> ImageResult:
        self._simulate_latency()
        return ImageResult(
            success=True,
            urls=[_MOCK_RESPONSES.get(model, "https://via.placeholder.com/512")],
            latency_ms=self._latency_ms,
        )

    def run_audio(self, credentials: Credential, model: str, params: dict,
                  file_path: Optional[str] = None) -> AudioResult:
        self._simulate_latency()
        op = params.get("operation", "transcription")
        if op == "speech":
            return AudioResult(success=True, audio_file="/tmp/mock_speech.mp3", latency_ms=self._latency_ms)
        return AudioResult(success=True, transcript=_MOCK_RESPONSES.get(model, "Mock transcription."),
                           latency_ms=self._latency_ms)
