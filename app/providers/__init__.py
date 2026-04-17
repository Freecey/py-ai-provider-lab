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


def build_adapter(provider):
    """Instantiate a provider adapter, forwarding base_url when supported."""
    cls = get_provider_class(provider.slug)
    if not cls:
        raise ValueError(f"No adapter registered for '{provider.slug}'")
    kwargs = {"timeout": provider.timeout_global, "proxy": provider.proxy or None}
    if provider.base_url:
        try:
            return cls(**kwargs, base_url=provider.base_url)
        except TypeError:
            pass
    return cls(**kwargs)


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
        register("minimax_cn", MinimaxProvider)
    except ImportError:
        logger.warning("minimax provider not available")
    try:
        from .zai import ZaiProvider
        register("zai", ZaiProvider)
    except ImportError:
        logger.warning("zai provider not available")


_auto_register()
