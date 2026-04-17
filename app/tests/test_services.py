"""Tests for business services using in-memory SQLite + MockProvider."""
import pytest
from unittest.mock import patch

from app.storage.db import Database
from app.storage.repositories.provider_repo import ProviderRepository
from app.storage.repositories.credential_repo import CredentialRepository
from app.storage.repositories.model_repo import ModelRepository
from app.models.provider import Provider
from app.models.credential import Credential
from app.models.model import Model


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    """Redirect all services to use an in-memory database."""
    db = Database(db_path=":memory:")
    db.connect()
    monkeypatch.setattr("app.storage.db._db", db)
    yield db
    db.close()


class TestProviderService:
    def test_create_and_list(self):
        from app.services.provider_service import ProviderService
        svc = ProviderService()
        p = svc.create_provider({"name": "Test Provider", "base_url": "https://test.api"})
        assert p.id is not None
        assert p.slug == "test-provider"
        providers = svc.list_providers()
        assert any(x.id == p.id for x in providers)

    def test_update(self):
        from app.services.provider_service import ProviderService
        svc = ProviderService()
        p = svc.create_provider({"name": "Update Me", "base_url": "http://old"})
        updated = svc.update_provider(p.id, {"base_url": "http://new"})
        assert updated.base_url == "http://new"

    def test_delete(self):
        from app.services.provider_service import ProviderService
        svc = ProviderService()
        p = svc.create_provider({"name": "Delete Me"})
        assert svc.delete_provider(p.id) is True
        assert svc.get_provider(p.id) is None

    def test_health_check_mock(self):
        from app.services.provider_service import ProviderService
        from app.services.credential_service import CredentialService
        p_svc = ProviderService()
        c_svc = CredentialService()
        p = p_svc.create_provider({"name": "Mock", "slug": "mock"})
        c = c_svc.create_credential({"provider_id": p.id, "name": "Mock Cred"})
        result = p_svc.health_check(p.id, c.id)
        assert result.status == "ok"


class TestCredentialService:
    def test_create_and_retrieve(self):
        from app.services.provider_service import ProviderService
        from app.services.credential_service import CredentialService
        p = ProviderService().create_provider({"name": "P", "slug": "p-cred-test"})
        svc = CredentialService()
        c = svc.create_credential({"provider_id": p.id, "name": "My Cred", "api_key": "sk-abc"})
        fetched = svc.get_credential(c.id)
        assert fetched.api_key == "sk-abc"

    def test_duplicate(self):
        from app.services.provider_service import ProviderService
        from app.services.credential_service import CredentialService
        p = ProviderService().create_provider({"name": "P2", "slug": "p2-dup"})
        svc = CredentialService()
        c = svc.create_credential({"provider_id": p.id, "name": "Original"})
        dup = svc.duplicate_credential(c.id)
        assert dup.id != c.id
        assert "copie" in dup.name


class TestModelService:
    def test_sync_with_mock(self):
        from app.services.provider_service import ProviderService
        from app.services.credential_service import CredentialService
        from app.services.model_service import ModelService
        p = ProviderService().create_provider({"name": "Mock", "slug": "mock"})
        c = CredentialService().create_credential({"provider_id": p.id, "name": "Mock Cred"})
        svc = ModelService()
        result = svc.sync_models(p.id, c.id)
        assert result.added == 3  # mock-text-v1, mock-image-v1, mock-audio-v1
        assert len(result.errors) == 0


class TestTestService:
    def test_run_text_with_mock(self):
        from app.services.provider_service import ProviderService
        from app.services.credential_service import CredentialService
        from app.services.model_service import ModelService
        from app.services.test_service import TestService
        p = ProviderService().create_provider({"name": "Mock", "slug": "mock"})
        c = CredentialService().create_credential({"provider_id": p.id, "name": "MockCred"})
        ModelService().sync_models(p.id, c.id)
        models = ModelService().list_models(provider_id=p.id)
        text_model = next((m for m in models if "text" in m.technical_name), None)
        assert text_model is not None
        run = TestService().run_text(c.id, text_model.id, {"user_prompt": "Hello"})
        assert run.status == "success"
        assert len(run.response_raw) > 0
