import time
import re
from typing import Any, Callable, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.utils.logger import get_logger

logger = get_logger("http_client")

_AUTH_HEADER_PATTERN = re.compile(r'Bearer\s+\S+|Basic\s+\S+', re.IGNORECASE)


def _mask_headers(headers: dict) -> dict:
    masked = {}
    for k, v in headers.items():
        if k.lower() in ("authorization", "x-api-key", "api-key"):
            masked[k] = "***"
        else:
            masked[k] = v
    return masked


class HttpClient:
    def __init__(self, timeout: int = 30, retry_count: int = 3,
                 retry_delay: float = 1.0, retry_backoff: float = 2.0,
                 proxy: Optional[str] = None):
        self.timeout = timeout
        self.proxy = proxy
        self._session = requests.Session()
        retry = Retry(
            total=retry_count,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        if proxy:
            self._session.proxies = {"http": proxy, "https": proxy}

    def request(self, method: str, url: str, headers: Optional[dict] = None,
                json: Optional[Any] = None, data: Optional[Any] = None,
                files: Optional[Any] = None, stream: bool = False,
                on_chunk: Optional[Callable[[str], None]] = None) -> requests.Response:
        start = time.monotonic()
        log_headers = _mask_headers(headers or {})
        logger.debug(f"{method} {url} headers={log_headers} json={json}")
        resp = self._session.request(
            method=method, url=url, headers=headers, json=json,
            data=data, files=files, timeout=self.timeout, stream=stream,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.debug(f"→ {resp.status_code} ({elapsed_ms}ms)")
        if stream and on_chunk:
            for line in resp.iter_lines():
                if line:
                    on_chunk(line.decode("utf-8") if isinstance(line, bytes) else line)
        return resp

    def get(self, url: str, headers: Optional[dict] = None, **kwargs) -> requests.Response:
        return self.request("GET", url, headers=headers, **kwargs)

    def post(self, url: str, headers: Optional[dict] = None, **kwargs) -> requests.Response:
        return self.request("POST", url, headers=headers, **kwargs)

    def close(self) -> None:
        self._session.close()
