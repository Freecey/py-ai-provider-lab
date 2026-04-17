"""
Z.ai provider adapter.
[PARTIEL] — Documentation partielle au moment de l'implémentation.
Basé sur une API compatible OpenAI.
"""
from app.models.credential import Credential
from app.models.results import ConnectionResult
from .openai_compat import OpenAICompatProvider

_ZAI_BASE = "https://api.z.ai/v1"


class ZaiProvider(OpenAICompatProvider):
    slug = "zai"

    def __init__(self, timeout: int = 30, retry_count: int = 3, proxy=None):
        super().__init__(base_url=_ZAI_BASE, timeout=timeout, retry_count=retry_count, proxy=proxy)

    def test_connection(self, credentials: Credential) -> ConnectionResult:
        result = super().test_connection(credentials)
        if not result.success:
            result.message = f"[PARTIEL] {result.message}"
        return result
