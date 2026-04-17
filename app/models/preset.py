from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Preset:
    id: Optional[int] = None
    name: str = ""
    modality: str = "text"          # text|image|audio|video
    model_id: Optional[int] = None  # nullable — preset can be generic
    params: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
