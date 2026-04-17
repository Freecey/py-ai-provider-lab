import time
from typing import Callable, Optional

from app.models.credential import Credential
from app.models.results import ConnectionResult, TextResult
from app.utils.http_client import HttpClient
from app.utils.logger import get_logger
from .base import BaseProvider

logger = get_logger("provider.openai_compat")


class OpenAICompatProvider(BaseProvider):
    """Generic adapter for any OpenAI-compatible REST API."""

    slug = "openai_compat"

    def __init__(self, base_url: str = "", timeout: int = 30,
                 retry_count: int = 3, proxy: Optional[str] = None):
        self._base_url = base_url.rstrip("/")
        self._http = HttpClient(timeout=timeout, retry_count=retry_count, proxy=proxy)

    def _headers(self, credentials: Credential) -> dict:
        key = credentials.api_key or credentials.bearer_token
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        if credentials.org_id:
            headers["OpenAI-Organization"] = credentials.org_id
        if credentials.project_id:
            headers["OpenAI-Project"] = credentials.project_id
        return headers

    def test_connection(self, credentials: Credential) -> ConnectionResult:
        start = time.monotonic()
        try:
            resp = self._http.get(f"{self._base_url}/models", headers=self._headers(credentials))
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code == 200:
                return ConnectionResult(success=True, message="OK", latency_ms=elapsed)
            return ConnectionResult(success=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                                    latency_ms=elapsed)
        except Exception as e:
            return ConnectionResult(success=False, message=str(e))

    def list_models(self, credentials: Credential) -> list:
        try:
            resp = self._http.get(f"{self._base_url}/models", headers=self._headers(credentials))
            if resp.status_code != 200:
                return []
            data = resp.json()
            return [
                {"technical_name": m["id"], "display_name": m.get("name", m["id"]), "type": "text",
                 "capabilities": self.normalize_capabilities(m)}
                for m in data.get("data", [])
            ]
        except Exception as e:
            logger.error(f"list_models error: {e}")
            return []

    def run_text(self, credentials: Credential, model: str, params: dict,
                 on_chunk: Optional[Callable[[str], None]] = None) -> TextResult:
        start = time.monotonic()
        payload = self._build_text_payload(model, params)
        stream = bool(on_chunk)
        payload["stream"] = stream

        collected_content = []
        raw_response = {}

        try:
            if stream and on_chunk:
                resp = self._http.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(credentials),
                    json=payload, stream=True,
                )
                import json as _json
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line = line.decode() if isinstance(line, bytes) else line
                    if line.startswith("data: "):
                        chunk_str = line[6:]
                        if chunk_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = _json.loads(chunk_str)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                collected_content.append(delta)
                                on_chunk(delta)
                        except Exception:
                            pass
                content = "".join(collected_content)
                elapsed = int((time.monotonic() - start) * 1000)
                return TextResult(success=True, content=content, model=model, latency_ms=elapsed)
            else:
                resp = self._http.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(credentials),
                    json=payload,
                )
                elapsed = int((time.monotonic() - start) * 1000)
                if resp.status_code != 200:
                    return TextResult(success=False, error=f"HTTP {resp.status_code}: {resp.text[:500]}",
                                      latency_ms=elapsed)
                data = resp.json()
                raw_response = data
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                return TextResult(
                    success=True, content=content, model=model,
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    total_tokens=usage.get("total_tokens"),
                    latency_ms=elapsed, raw_response=raw_response,
                )
        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            return TextResult(success=False, error=str(e), latency_ms=elapsed)

    def _build_text_payload(self, model: str, params: dict) -> dict:
        messages = []
        if params.get("system_prompt"):
            messages.append({"role": "system", "content": params["system_prompt"]})
        messages.append({"role": "user", "content": params.get("user_prompt", params.get("prompt", ""))})

        payload: dict = {"model": model, "messages": messages}
        for key in ("temperature", "top_p", "max_tokens", "frequency_penalty",
                    "presence_penalty", "seed"):
            if key in params and params[key] is not None:
                payload[key] = params[key]
        if params.get("stop_sequences"):
            payload["stop"] = params["stop_sequences"]
        if params.get("json_mode"):
            payload["response_format"] = {"type": "json_object"}
        return payload
