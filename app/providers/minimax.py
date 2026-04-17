import time
from typing import Callable, Optional

from app.models.credential import Credential
from app.models.results import ConnectionResult, TextResult, AsyncTaskRef, TaskStatus
from app.utils.http_client import HttpClient
from app.utils.logger import get_logger
from .base import BaseProvider

logger = get_logger("provider.minimax")

_MINIMAX_BASE = "https://api.minimax.chat/v1"


class MinimaxProvider(BaseProvider):
    slug = "minimax"

    def __init__(self, timeout: int = 60, retry_count: int = 3, proxy: Optional[str] = None):
        self._http = HttpClient(timeout=timeout, retry_count=retry_count, proxy=proxy)

    def _headers(self, credentials: Credential) -> dict:
        return {
            "Authorization": f"Bearer {credentials.api_key}",
            "Content-Type": "application/json",
        }

    def test_connection(self, credentials: Credential) -> ConnectionResult:
        start = time.monotonic()
        try:
            resp = self._http.get(f"{_MINIMAX_BASE}/models/list", headers=self._headers(credentials))
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code == 200:
                return ConnectionResult(success=True, message="OK", latency_ms=elapsed)
            return ConnectionResult(success=False, message=f"HTTP {resp.status_code}", latency_ms=elapsed)
        except Exception as e:
            return ConnectionResult(success=False, message=str(e))

    def list_models(self, credentials: Credential) -> list:
        try:
            resp = self._http.get(f"{_MINIMAX_BASE}/models/list", headers=self._headers(credentials))
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {"technical_name": m.get("model_id", m.get("id", "")),
                     "display_name": m.get("model_name", ""),
                     "type": "text", "capabilities": ["chat", "streaming"]}
                    for m in data.get("models", data.get("data", []))
                ]
        except Exception as e:
            logger.error(f"list_models: {e}")
        return []

    def run_text(self, credentials: Credential, model: str, params: dict,
                 on_chunk: Optional[Callable] = None) -> TextResult:
        start = time.monotonic()
        messages = []
        if params.get("system_prompt"):
            messages.append({"role": "system", "content": params["system_prompt"]})
        messages.append({"role": "user", "content": params.get("user_prompt", params.get("prompt", ""))})
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": params.get("max_tokens", 2048),
        }
        if params.get("temperature") is not None:
            payload["temperature"] = params["temperature"]
        try:
            resp = self._http.post(f"{_MINIMAX_BASE}/text/chatcompletion_v2",
                                   headers=self._headers(credentials), json=payload)
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code != 200:
                return TextResult(success=False, error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                                  latency_ms=elapsed)
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return TextResult(success=True, content=content, model=model, latency_ms=elapsed, raw_response=data)
        except Exception as e:
            return TextResult(success=False, error=str(e), latency_ms=int((time.monotonic() - start) * 1000))

    def run_video(self, credentials: Credential, model: str, params: dict) -> AsyncTaskRef:
        """Submit async video generation task."""
        payload = {"model": model, "prompt": params.get("prompt", "")}
        if params.get("duration"):
            payload["duration"] = params["duration"]
        try:
            resp = self._http.post(f"{_MINIMAX_BASE}/video_generation",
                                   headers=self._headers(credentials), json=payload)
            data = resp.json()
            task_id = data.get("task_id", "")
            return AsyncTaskRef(provider_task_id=task_id, poll_interval_s=15, timeout_s=600)
        except Exception as e:
            raise RuntimeError(f"MiniMax video submission failed: {e}") from e

    def poll_task(self, credentials: Credential, task_ref: AsyncTaskRef) -> TaskStatus:
        try:
            resp = self._http.get(
                f"{_MINIMAX_BASE}/query/video_generation?task_id={task_ref.provider_task_id}",
                headers=self._headers(credentials),
            )
            data = resp.json()
            status = data.get("status", "Unknown")
            if status in ("Success", "Finished"):
                from app.models.results import VideoResult
                url = data.get("file_id", "")
                return TaskStatus(provider_task_id=task_ref.provider_task_id, status="done",
                                  result=VideoResult(success=True, video_file=url), raw_response=data)
            elif status in ("Fail", "Failed"):
                return TaskStatus(provider_task_id=task_ref.provider_task_id, status="failed",
                                  error=data.get("message", ""), raw_response=data)
            return TaskStatus(provider_task_id=task_ref.provider_task_id, status="running", raw_response=data)
        except Exception as e:
            return TaskStatus(provider_task_id=task_ref.provider_task_id, status="failed", error=str(e))
