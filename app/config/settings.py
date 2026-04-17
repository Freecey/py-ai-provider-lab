import configparser
import os
from dataclasses import dataclass
from .constants import (
    DEFAULT_DATA_DIR, DEFAULT_LOG_LEVEL, DEFAULT_THEME,
    DEFAULT_LANG, DEFAULT_NETWORK_TIMEOUT, DEFAULT_SANDBOX_MODE,
)

_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "config.ini")


@dataclass
class Settings:
    data_dir: str = DEFAULT_DATA_DIR
    log_level: str = DEFAULT_LOG_LEVEL
    theme: str = DEFAULT_THEME
    lang: str = DEFAULT_LANG
    network_timeout: int = DEFAULT_NETWORK_TIMEOUT
    sandbox_mode: bool = DEFAULT_SANDBOX_MODE


def load_settings(config_path: str = _CONFIG_FILE) -> Settings:
    cfg = configparser.ConfigParser()
    cfg.read(config_path)
    section = "app"

    def _get(key, default):
        return cfg.get(section, key, fallback=default)

    s = Settings(
        data_dir=os.environ.get("APP_DATA_DIR", _get("data_dir", DEFAULT_DATA_DIR)),
        log_level=os.environ.get("APP_LOG_LEVEL", _get("log_level", DEFAULT_LOG_LEVEL)).upper(),
        theme=os.environ.get("APP_THEME", _get("theme", DEFAULT_THEME)),
        lang=os.environ.get("APP_LANG", _get("lang", DEFAULT_LANG)),
        network_timeout=int(os.environ.get("APP_NETWORK_TIMEOUT", _get("network_timeout", str(DEFAULT_NETWORK_TIMEOUT)))),
        sandbox_mode=os.environ.get("APP_SANDBOX_MODE", _get("sandbox_mode", str(DEFAULT_SANDBOX_MODE))).lower() in ("true", "1", "yes"),
    )
    return s


_settings: "Settings | None" = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
