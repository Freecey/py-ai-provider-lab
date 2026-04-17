import re
from typing import Optional

from app.models.provider import Provider
from app.models.results import HealthStatus
from app.storage.db import get_conn
from app.storage.repositories.provider_repo import ProviderRepository
from app.storage.repositories.credential_repo import CredentialRepository
from app.providers import build_adapter
from app.utils.logger import get_logger

logger = get_logger("service.provider")


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class ProviderService:
    def __init__(self):
        self._repo = ProviderRepository(get_conn())
        self._cred_repo = CredentialRepository(get_conn())

    def list_providers(self, active_only: bool = False) -> list[Provider]:
        return self._repo.list(active_only=active_only)

    def get_provider(self, id: int) -> Optional[Provider]:
        return self._repo.get_by_id(id)

    def create_provider(self, data: dict) -> Provider:
        p = Provider(**{k: v for k, v in data.items() if hasattr(Provider, k)})
        if not p.slug:
            p.slug = _slugify(p.name)
        return self._repo.create(p)

    def update_provider(self, id: int, data: dict) -> Optional[Provider]:
        p = self._repo.get_by_id(id)
        if not p:
            return None
        for k, v in data.items():
            if hasattr(p, k):
                setattr(p, k, v)
        return self._repo.update(p)

    def delete_provider(self, id: int) -> bool:
        return self._repo.delete(id)

    def health_check(self, provider_id: int, credential_id: int) -> HealthStatus:
        provider = self._repo.get_by_id(provider_id)
        credential = self._cred_repo.get_by_id(credential_id)
        if not provider or not credential:
            return HealthStatus(provider_id=provider_id, status="untested",
                                message="Provider or credential not found")
        try:
            adapter = build_adapter(provider)
            result = adapter.test_connection(credential)
            status = "ok" if result.success else "endpoint_ko"
            if not result.success and "auth" in result.message.lower():
                status = "auth_invalid"
            if not result.success and "timeout" in result.message.lower():
                status = "timeout"
            self._cred_repo.update_validity(credential_id, "ok" if result.success else "invalid")
            return HealthStatus(provider_id=provider_id, status=status,
                                message=result.message, latency_ms=result.latency_ms)
        except Exception as e:
            logger.error(f"health_check error: {e}")
            return HealthStatus(provider_id=provider_id, status="endpoint_ko", message=str(e))

    def health_check_all(self) -> dict[int, HealthStatus]:
        results = {}
        for provider in self._repo.list(active_only=True):
            creds = self._cred_repo.list(provider_id=provider.id)
            if not creds:
                results[provider.id] = HealthStatus(provider_id=provider.id, status="untested",
                                                     message="No credentials configured")
                continue
            active_creds = [c for c in creds if c.active]
            cred = active_creds[0] if active_creds else creds[0]
            results[provider.id] = self.health_check(provider.id, cred.id)
        return results
