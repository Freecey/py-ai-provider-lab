from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Credential:
    id: Optional[int] = None
    provider_id: Optional[int] = None
    name: str = ""
    active: bool = True
    validity: str = "untested"              # ok|invalid|untested
    api_key: str = ""                       # stored encrypted
    bearer_token: str = ""                  # stored encrypted
    oauth_access_token: str = ""            # stored encrypted
    oauth_refresh_token: str = ""           # stored encrypted
    oauth_client_id: str = ""
    oauth_client_secret: str = ""           # stored encrypted
    oauth_scopes: str = ""
    oauth_auth_url: str = ""
    oauth_token_endpoint: str = ""
    oauth_expires_at: Optional[datetime] = None
    org_id: str = ""
    project_id: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
