from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ModelCapability:
    id: Optional[int] = None
    model_id: Optional[int] = None
    capability: str = ""
    # Valid values: chat|reasoning|vision|image_gen|video_gen|video_understanding|
    #               transcription|speech|embeddings|tool_calling|json_output|streaming


@dataclass
class Model:
    id: Optional[int] = None
    provider_id: Optional[int] = None
    technical_name: str = ""
    display_name: str = ""
    type: str = "text"      # text|image|audio|video|multimodal|embedding|other
    active: bool = True
    favorite: bool = False
    rating: Optional[int] = None           # 1-5
    context_max: Optional[int] = None
    cost_input: Optional[float] = None
    cost_output: Optional[float] = None
    currency: str = "USD"
    rpm_limit: Optional[int] = None
    tpm_limit: Optional[int] = None
    tags: list = field(default_factory=list)
    notes: str = ""
    extra: dict = field(default_factory=dict)
    capabilities: list = field(default_factory=list)  # list[ModelCapability]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
