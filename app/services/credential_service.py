import copy
from typing import Optional

from app.models.credential import Credential
from app.models.results import ConnectionResult
from app.storage.db import get_conn
from app.storage.repositories.credential_repo import CredentialRepository
from app.storage.repositories.provider_repo import ProviderRepository
from app.providers import get_provider_class
from app.utils.logger import get_logger

logger = get_logger("service.credential")


class CredentialService:
    def __init__(self):
        self._repo = CredentialRepository(get_conn())
        self._p_repo = ProviderRepository(get_conn())

    def list_credentials(self, provider_id: Optional[int] = None) -> list[Credential]:
        return self._repo.list(provider_id=provider_id)

    def get_credential(self, id: int) -> Optional[Credential]:
        return self._repo.get_by_id(id)

    def create_credential(self, data: dict) -> Credential:
        c = Credential(**{k: v for k, v in data.items() if hasattr(Credential, k)})
        return self._repo.create(c)

    def update_credential(self, id: int, data: dict) -> Optional[Credential]:
        c = self._repo.get_by_id(id)
        if not c:
            return None
        for k, v in data.items():
            if hasattr(c, k):
                setattr(c, k, v)
        return self._repo.update(c)

    def delete_credential(self, id: int) -> bool:
        return self._repo.delete(id)

    def duplicate_credential(self, id: int) -> Optional[Credential]:
        c = self._repo.get_by_id(id)
        if not c:
            return None
        dup = copy.copy(c)
        dup.id = None
        dup.name = f"{c.name} (copie)"
        dup.validity = "untested"
        return self._repo.create(dup)

    def test_connection(self, credential_id: int) -> ConnectionResult:
        c = self._repo.get_by_id(credential_id)
        if not c:
            return ConnectionResult(success=False, message="Credential introuvable")
        provider = self._p_repo.get_by_id(c.provider_id)
        if not provider:
            return ConnectionResult(success=False, message="Provider introuvable")
        cls = get_provider_class(provider.slug)
        if not cls:
            return ConnectionResult(success=False, message=f"Pas d'adaptateur pour '{provider.slug}'")
        try:
            adapter = cls(timeout=provider.timeout_global, proxy=provider.proxy or None)
            result = adapter.test_connection(c)
            self._repo.update_validity(credential_id, "ok" if result.success else "invalid")
            return result
        except Exception as e:
            return ConnectionResult(success=False, message=str(e))

    def refresh_oauth_token(self, credential_id: int) -> Optional[Credential]:
        c = self._repo.get_by_id(credential_id)
        if not c:
            return None
        # OAuth2 token refresh — provider-specific, delegated to future implementation
        logger.warning(f"OAuth2 refresh not fully implemented for credential {credential_id}")
        return c
