from app.models.credential import Credential
from .openai_compat import OpenAICompatProvider

_DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class AlibabaProvider(OpenAICompatProvider):
    """Alibaba Cloud DashScope — OpenAI-compatible mode."""
    slug = "alibaba"

    def __init__(self, timeout: int = 60, retry_count: int = 3, proxy=None):
        super().__init__(base_url=_DASHSCOPE_BASE, timeout=timeout,
                         retry_count=retry_count, proxy=proxy)

    def normalize_capabilities(self, raw: dict) -> list[str]:
        caps = ["chat", "streaming"]
        model_id = raw.get("id", "")
        if "vl" in model_id or "vision" in model_id:
            caps.append("vision")
        if "qwen" in model_id:
            caps.append("tool_calling")
            caps.append("json_output")
        return list(set(caps))
