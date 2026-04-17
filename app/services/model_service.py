from typing import Optional

from app.models.model import Model, ModelCapability
from app.models.results import SyncResult
from app.storage.db import get_conn
from app.storage.repositories.model_repo import ModelRepository
from app.storage.repositories.credential_repo import CredentialRepository
from app.storage.repositories.provider_repo import ProviderRepository
from app.providers import build_adapter
from app.utils.logger import get_logger

logger = get_logger("service.model")


class ModelService:
    def __init__(self):
        self._repo = ModelRepository(get_conn())
        self._p_repo = ProviderRepository(get_conn())
        self._c_repo = CredentialRepository(get_conn())

    def list_models(self, provider_id: Optional[int] = None, type: Optional[str] = None,
                    active_only: bool = True) -> list[Model]:
        return self._repo.list(provider_id=provider_id, type=type, active_only=active_only)

    def get_model(self, id: int) -> Optional[Model]:
        return self._repo.get_by_id(id)

    def create_model(self, data: dict) -> Model:
        caps_raw = data.pop("capabilities", [])
        m = Model(**{k: v for k, v in data.items() if hasattr(Model, k)})
        m.capabilities = [ModelCapability(capability=c) if isinstance(c, str) else c for c in caps_raw]
        return self._repo.create(m)

    def update_model(self, id: int, data: dict) -> Optional[Model]:
        m = self._repo.get_by_id(id)
        if not m:
            return None
        caps_raw = data.pop("capabilities", None)
        for k, v in data.items():
            if hasattr(m, k):
                setattr(m, k, v)
        if caps_raw is not None:
            m.capabilities = [ModelCapability(capability=c) if isinstance(c, str) else c for c in caps_raw]
        return self._repo.update(m)

    def delete_model(self, id: int) -> bool:
        return self._repo.delete(id)

    def sync_models(self, provider_id: int, credential_id: int) -> SyncResult:
        provider = self._p_repo.get_by_id(provider_id)
        credential = self._c_repo.get_by_id(credential_id)
        if not provider or not credential:
            return SyncResult(errors=["Provider or credential not found"])
        try:
            adapter = build_adapter(provider)
            remote_models = adapter.list_models(credential)
        except Exception as e:
            return SyncResult(errors=[str(e)])

        result = SyncResult()
        existing = {m.technical_name: m for m in self._repo.list(provider_id=provider_id, active_only=False)}

        for rm in remote_models:
            tech = rm.get("technical_name", "")
            if not tech:
                continue
            caps = [ModelCapability(capability=c) for c in rm.get("capabilities", [])]
            if tech in existing:
                m = existing[tech]
                m.display_name = rm.get("display_name", m.display_name)
                m.capabilities = caps
                self._repo.update(m)
                result.updated += 1
            else:
                m = Model(
                    provider_id=provider_id,
                    technical_name=tech,
                    display_name=rm.get("display_name", tech),
                    type=rm.get("type", "text"),
                    capabilities=caps,
                )
                self._repo.create(m)
                result.added += 1
        return result

    def rate_model(self, model_id: int, rating: int) -> Optional[Model]:
        m = self._repo.get_by_id(model_id)
        if not m:
            return None
        m.rating = max(1, min(5, rating))
        return self._repo.update(m)
