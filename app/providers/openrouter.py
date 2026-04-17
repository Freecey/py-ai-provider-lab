from app.models.credential import Credential
from .openai_compat import OpenAICompatProvider

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class OpenRouterProvider(OpenAICompatProvider):
    slug = "openrouter"

    def __init__(self, timeout: int = 30, retry_count: int = 3, proxy=None):
        super().__init__(base_url=_OPENROUTER_BASE, timeout=timeout,
                         retry_count=retry_count, proxy=proxy)

    def _headers(self, credentials: Credential) -> dict:
        headers = super()._headers(credentials)
        headers["HTTP-Referer"] = "https://github.com/py-ai-provider-lab"
        headers["X-Title"] = "py-ai-provider-lab"
        return headers

    def normalize_capabilities(self, raw: dict) -> list[str]:
        caps = ["chat", "streaming"]
        arch = raw.get("architecture", {})
        if arch.get("input_modalities") and "image" in arch.get("input_modalities", []):
            caps.append("vision")
        if "tool" in str(raw.get("id", "")):
            caps.append("tool_calling")
        return list(set(caps))
