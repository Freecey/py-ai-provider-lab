from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PromptTemplate:
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    modality: str = "text"          # text|image|audio|video
    category: str = ""
    tags: list = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
