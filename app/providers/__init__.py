from .mock import MockProvider
from .openai_compat import OpenAICompatProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from app.utils.logger import get_logger

_REGISTRY: dict = {}
logger = get_logger("providers")


def register(slug: str, provider_class) -> None:
    _REGISTRY[slug] = provider_class


def get_provider_class(slug: str):
    return _REGISTRY.get(slug)


def _auto_register() -> None:
    register("mock", MockProvider)
    register("openai", OpenAIProvider)
    register("openai_compat", OpenAICompatProvider)
    register("anthropic", AnthropicProvider)
    try:
        from .openrouter import OpenRouterProvider
        register("openrouter", OpenRouterProvider)
    except ImportError:
        logger.warning("openrouter provider not available")
    try:
        from .alibaba import AlibabaProvider
        register("alibaba", AlibabaProvider)
    except ImportError:
        logger.warning("alibaba provider not available")
    try:
        from .minimax import MinimaxProvider
        register("minimax", MinimaxProvider)
    except ImportError:
        logger.warning("minimax provider not available")
    try:
        from .zai import ZaiProvider
        register("zai", ZaiProvider)
    except ImportError:
        logger.warning("zai provider not available")


_auto_register()
