from abc import ABC, abstractmethod
from typing import Callable, Optional

from app.models.credential import Credential
from app.models.results import (
    ConnectionResult, TextResult, ImageResult, AudioResult,
    VideoResult, AsyncTaskRef, TaskStatus,
)


class BaseProvider(ABC):
    """Abstract base class for all AI provider adapters."""

    slug: str = ""

    @abstractmethod
    def test_connection(self, credentials: Credential) -> ConnectionResult:
        ...

    @abstractmethod
    def list_models(self, credentials: Credential) -> list:
        """Return list of ModelInfo dicts: {technical_name, display_name, type, capabilities}"""
        ...

    def run_text(self, credentials: Credential, model: str, params: dict,
                 on_chunk: Optional[Callable[[str], None]] = None) -> TextResult:
        raise NotImplementedError(f"{self.__class__.__name__} does not support text generation")

    def run_image(self, credentials: Credential, model: str, params: dict) -> ImageResult:
        raise NotImplementedError(f"{self.__class__.__name__} does not support image generation")

    def run_audio(self, credentials: Credential, model: str, params: dict,
                  file_path: Optional[str] = None) -> AudioResult:
        raise NotImplementedError(f"{self.__class__.__name__} does not support audio processing")

    def run_video(self, credentials: Credential, model: str,
                  params: dict) -> "VideoResult | AsyncTaskRef":
        raise NotImplementedError(f"{self.__class__.__name__} does not support video generation")

    def poll_task(self, credentials: Credential, task_ref: AsyncTaskRef) -> TaskStatus:
        raise NotImplementedError(f"{self.__class__.__name__} does not support async task polling")

    def normalize_capabilities(self, raw: dict) -> list[str]:
        return []
