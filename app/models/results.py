from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConnectionResult:
    success: bool = False
    message: str = ""
    latency_ms: Optional[int] = None
    details: dict = field(default_factory=dict)


@dataclass
class TextResult:
    success: bool = False
    content: str = ""
    model: str = ""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_estimated: Optional[float] = None
    latency_ms: Optional[int] = None
    raw_response: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class ImageResult:
    success: bool = False
    urls: list = field(default_factory=list)    # remote URLs
    files: list = field(default_factory=list)   # local file paths
    latency_ms: Optional[int] = None
    cost_estimated: Optional[float] = None
    raw_response: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class AudioResult:
    success: bool = False
    transcript: str = ""
    audio_file: str = ""            # local path for TTS output
    latency_ms: Optional[int] = None
    cost_estimated: Optional[float] = None
    raw_response: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class VideoResult:
    success: bool = False
    video_file: str = ""
    latency_ms: Optional[int] = None
    cost_estimated: Optional[float] = None
    raw_response: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class AsyncTaskRef:
    provider_task_id: str = ""
    poll_interval_s: int = 10
    timeout_s: int = 600
    raw_response: dict = field(default_factory=dict)


@dataclass
class TaskStatus:
    provider_task_id: str = ""
    status: str = "pending"         # pending|running|done|failed
    result: Optional[VideoResult] = None
    error: str = ""
    raw_response: dict = field(default_factory=dict)


@dataclass
class SyncResult:
    added: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)


@dataclass
class HealthStatus:
    provider_id: Optional[int] = None
    status: str = "untested"        # ok|auth_invalid|endpoint_ko|timeout|untested
    message: str = ""
    latency_ms: Optional[int] = None
