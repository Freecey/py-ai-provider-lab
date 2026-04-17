from __future__ import annotations

import time
from typing import Callable, Optional

from app.models.credential import Credential
from app.models.results import ConnectionResult, TextResult, AsyncTaskRef, TaskStatus
from app.utils.http_client import HttpClient
from app.utils.logger import get_logger
from .base import BaseProvider

logger = get_logger("provider.minimax")

_MINIMAX_GLOBAL = "https://api.minimax.io/v1"
_MINIMAX_CN = "https://api.minimax.chat/v1"

KNOWN_MODELS = [
    {"technical_name": "minimax-m2.7", "display_name": "MiniMax M2.7", "type": "text",
     "capabilities": ["chat", "streaming", "tool_calling", "json_output", "vision"]},
    {"technical_name": "minimax-m2.5", "display_name": "MiniMax M2.5", "type": "text",
     "capabilities": ["chat", "streaming", "tool_calling", "json_output"]},
    {"technical_name": "minimax-m2.5-highspeed", "display_name": "MiniMax M2.5 High Speed", "type": "text",
     "capabilities": ["chat", "streaming"]},
    {"technical_name": "abab6.5s", "display_name": "abab6.5s (200k ctx)", "type": "text",
     "capabilities": ["chat", "streaming", "tool_calling"]},
    {"technical_name": "abab6.5", "display_name": "abab6.5", "type": "text",
     "capabilities": ["chat", "streaming"]},
    {"technical_name": "video-01", "display_name": "Video-01", "type": "video",
     "capabilities": ["video_gen"]},
]


class MinimaxProvider(BaseProvider):
    slug = "minimax"

    def __init__(self, timeout: int = 60, retry_count: int = 3,
                 proxy: Optional[str] = None, base_url: Optional[str] = None):
        self._base = (base_url or _MINIMAX_GLOBAL).rstrip("/")
        self._http = HttpClient(timeout=timeout, retry_count=retry_count, proxy=proxy)

    def _headers(self, credentials: Credential) -> dict:
        return {
            "Authorization": f"Bearer {credentials.api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, credentials: Credential, path: str) -> str:
        """Append GroupId query param if stored in credential.org_id."""
        url = f"{self._base}{path}"
        group_id = (credentials.org_id or "").strip()
        if group_id:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}GroupId={group_id}"
        return url

    def test_connection(self, credentials: Credential) -> ConnectionResult:
        start = time.monotonic()
        try:
            resp = self._http.get(
                self._url(credentials, "/models/list"),
                headers=self._headers(credentials),
            )
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code == 200:
                return ConnectionResult(success=True, message="OK", latency_ms=elapsed)
            return ConnectionResult(
                success=False,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                latency_ms=elapsed,
            )
        except Exception as e:
            return ConnectionResult(success=False, message=str(e))

    def list_models(self, credentials: Credential) -> list:
        try:
            resp = self._http.get(
                self._url(credentials, "/models/list"),
                headers=self._headers(credentials),
            )
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {
                        "technical_name": m.get("model_id", m.get("id", "")),
                        "display_name": m.get("model_name", m.get("id", "")),
                        "type": "text",
                        "capabilities": ["chat", "streaming"],
                    }
                    for m in data.get("models", data.get("data", []))
                ]
        except Exception as e:
            logger.error(f"list_models: {e}")
        return list(KNOWN_MODELS)

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
            resp = self._http.post(
                self._url(credentials, "/text/chatcompletion_v2"),
                headers=self._headers(credentials),
                json=payload,
            )
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code != 200:
                return TextResult(
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                    latency_ms=elapsed,
                )
            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return TextResult(success=True, content=content, model=model,
                              latency_ms=elapsed, raw_response=data)
        except Exception as e:
            return TextResult(success=False, error=str(e),
                              latency_ms=int((time.monotonic() - start) * 1000))

    def run_video(self, credentials: Credential, model: str, params: dict) -> AsyncTaskRef:
        payload = {"model": model, "prompt": params.get("prompt", "")}
        if params.get("duration"):
            payload["duration"] = params["duration"]
        try:
            resp = self._http.post(
                self._url(credentials, "/video_generation"),
                headers=self._headers(credentials),
                json=payload,
            )
            data = resp.json()
            task_id = data.get("task_id", "")
            return AsyncTaskRef(provider_task_id=task_id, poll_interval_s=15, timeout_s=600)
        except Exception as e:
            raise RuntimeError(f"MiniMax video submission failed: {e}") from e

    def poll_task(self, credentials: Credential, task_ref: AsyncTaskRef) -> TaskStatus:
        try:
            resp = self._http.get(
                self._url(credentials, f"/query/video_generation?task_id={task_ref.provider_task_id}"),
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
            return TaskStatus(provider_task_id=task_ref.provider_task_id, status="running",
                              raw_response=data)
        except Exception as e:
            return TaskStatus(provider_task_id=task_ref.provider_task_id, status="failed", error=str(e))
