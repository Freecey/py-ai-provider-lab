from app.models.credential import Credential
from app.models.results import ConnectionResult, ImageResult
from app.utils.http_client import HttpClient
from app.utils.logger import get_logger
from .openai_compat import OpenAICompatProvider

logger = get_logger("provider.openai")

_OPENAI_BASE = "https://api.openai.com/v1"


class OpenAIProvider(OpenAICompatProvider):
    slug = "openai"

    def __init__(self, timeout: int = 30, retry_count: int = 3, proxy=None):
        super().__init__(base_url=_OPENAI_BASE, timeout=timeout, retry_count=retry_count, proxy=proxy)

    def normalize_capabilities(self, raw: dict) -> list[str]:
        caps = ["chat"]
        model_id = raw.get("id", "")
        if "gpt" in model_id or "o1" in model_id or "o3" in model_id:
            caps.append("chat")
        if "vision" in model_id or "4o" in model_id:
            caps.append("vision")
        if "tts" in model_id:
            caps.append("speech")
        if "whisper" in model_id:
            caps.append("transcription")
        if "dall-e" in model_id:
            caps.append("image_gen")
        if "embedding" in model_id:
            caps.append("embeddings")
        caps.append("tool_calling")
        caps.append("json_output")
        caps.append("streaming")
        return list(set(caps))

    def run_image(self, credentials: Credential, model: str, params: dict) -> ImageResult:
        import time
        start = time.monotonic()
        payload = {
            "model": model,
            "prompt": params.get("prompt", ""),
            "n": params.get("n", 1),
            "size": params.get("size", "1024x1024"),
        }
        if params.get("quality"):
            payload["quality"] = params["quality"]
        if params.get("output_format"):
            payload["response_format"] = params["output_format"]

        try:
            resp = self._http.post(
                f"{self._base_url}/images/generations",
                headers=self._headers(credentials),
                json=payload,
            )
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code != 200:
                return ImageResult(success=False, error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                                   latency_ms=elapsed)
            data = resp.json()
            urls = [item.get("url", "") for item in data.get("data", [])]
            return ImageResult(success=True, urls=urls, latency_ms=elapsed, raw_response=data)
        except Exception as e:
            return ImageResult(success=False, error=str(e))
