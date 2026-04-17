from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Provider:
    id: Optional[int] = None
    name: str = ""
    slug: str = ""
    active: bool = True
    base_url: str = ""
    endpoints: dict = field(default_factory=dict)       # JSON: {modality: url}
    api_version: str = ""
    auth_type: str = "api_key"                          # api_key|bearer|oauth2|custom
    custom_headers: dict = field(default_factory=dict)  # JSON
    timeout_global: int = 30
    timeout_per_modality: dict = field(default_factory=dict)  # JSON
    retry_count: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    proxy: str = ""
    notes: str = ""
    extra_fields: dict = field(default_factory=dict)    # JSON
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
