from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TestRun:
    id: Optional[int] = None
    provider_id: Optional[int] = None
    credential_id: Optional[int] = None
    model_id: Optional[int] = None
    modality: str = "text"                  # text|image|audio|video
    params: dict = field(default_factory=dict)
    request_payload: dict = field(default_factory=dict)
    response_raw: str = ""
    response_files: list = field(default_factory=list)  # paths to media files
    latency_ms: Optional[int] = None
    cost_estimated: Optional[float] = None
    currency: str = "USD"
    status: str = "pending"                 # success|error|pending|cancelled
    error_message: str = ""
    rating: Optional[int] = None           # 1-5
    rating_notes: str = ""
    created_at: Optional[datetime] = None
