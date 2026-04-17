import time
from typing import Callable, Optional

from app.models.credential import Credential
from app.models.results import ConnectionResult, TextResult
from app.utils.http_client import HttpClient
from app.utils.logger import get_logger
from .base import BaseProvider

logger = get_logger("provider.anthropic")

_ANTHROPIC_BASE = "https://api.anthropic.com"
_API_VERSION = "2023-06-01"

_KNOWN_MODELS = [
    {"technical_name": "claude-opus-4-7", "display_name": "Claude Opus 4.7", "type": "text",
     "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming", "reasoning"]},
    {"technical_name": "claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6", "type": "text",
     "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming"]},
    {"technical_name": "claude-haiku-4-5-20251001", "display_name": "Claude Haiku 4.5", "type": "text",
     "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming"]},
]


class AnthropicProvider(BaseProvider):
    slug = "anthropic"

    def __init__(self, timeout: int = 30, retry_count: int = 3, proxy: Optional[str] = None):
        self._http = HttpClient(timeout=timeout, retry_count=retry_count, proxy=proxy)

    def _headers(self, credentials: Credential) -> dict:
        return {
            "x-api-key": credentials.api_key,
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        }

    def test_connection(self, credentials: Credential) -> ConnectionResult:
        start = time.monotonic()
        try:
            resp = self._http.post(
                f"{_ANTHROPIC_BASE}/v1/messages",
                headers=self._headers(credentials),
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1,
                      "messages": [{"role": "user", "content": "ping"}]},
            )
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code in (200, 400):
                return ConnectionResult(success=True, message="OK", latency_ms=elapsed)
            return ConnectionResult(success=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                                    latency_ms=elapsed)
        except Exception as e:
            return ConnectionResult(success=False, message=str(e))

    def list_models(self, credentials: Credential) -> list:
        try:
            resp = self._http.get(f"{_ANTHROPIC_BASE}/v1/models", headers=self._headers(credentials))
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {"technical_name": m["id"], "display_name": m.get("display_name", m["id"]),
                     "type": "text", "capabilities": ["chat", "streaming", "tool_calling", "json_output"]}
                    for m in data.get("data", [])
                ]
        except Exception:
            pass
        return list(_KNOWN_MODELS)

    def run_text(self, credentials: Credential, model: str, params: dict,
                 on_chunk: Optional[Callable[[str], None]] = None) -> TextResult:
        start = time.monotonic()
        messages = [{"role": "user", "content": params.get("user_prompt", params.get("prompt", ""))}]
        payload: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": params.get("max_tokens", 4096),
        }
        if params.get("system_prompt"):
            payload["system"] = params["system_prompt"]
        for key in ("temperature", "top_p"):
            if key in params and params[key] is not None:
                payload[key] = params[key]
        stream = bool(on_chunk)

        try:
            if stream and on_chunk:
                payload["stream"] = True
                resp = self._http.post(
                    f"{_ANTHROPIC_BASE}/v1/messages",
                    headers=self._headers(credentials),
                    json=payload, stream=True,
                )
                import json as _json
                collected = []
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line = line.decode() if isinstance(line, bytes) else line
                    if line.startswith("data:"):
                        try:
                            evt = _json.loads(line[5:].strip())
                            if evt.get("type") == "content_block_delta":
                                delta = evt["delta"].get("text", "")
                                collected.append(delta)
                                on_chunk(delta)
                        except Exception:
                            pass
                content = "".join(collected)
                elapsed = int((time.monotonic() - start) * 1000)
                return TextResult(success=True, content=content, model=model, latency_ms=elapsed)
            else:
                resp = self._http.post(
                    f"{_ANTHROPIC_BASE}/v1/messages",
                    headers=self._headers(credentials),
                    json=payload,
                )
                elapsed = int((time.monotonic() - start) * 1000)
                if resp.status_code != 200:
                    return TextResult(success=False, error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                                      latency_ms=elapsed)
                data = resp.json()
                content = "".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")
                usage = data.get("usage", {})
                return TextResult(
                    success=True, content=content, model=model,
                    prompt_tokens=usage.get("input_tokens"),
                    completion_tokens=usage.get("output_tokens"),
                    total_tokens=(usage.get("input_tokens", 0) + usage.get("output_tokens", 0)),
                    latency_ms=elapsed, raw_response=data,
                )
        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            return TextResult(success=False, error=str(e), latency_ms=elapsed)
