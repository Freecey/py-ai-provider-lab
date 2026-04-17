from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AsyncTask:
    id: Optional[int] = None
    test_run_id: Optional[int] = None
    provider_task_id: str = ""
    status: str = "pending"         # pending|running|done|failed
    poll_interval_s: int = 10
    timeout_s: int = 600
    last_polled_at: Optional[datetime] = None
    result: dict = field(default_factory=dict)
    error: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
