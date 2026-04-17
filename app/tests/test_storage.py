"""Tests for repositories using an in-memory SQLite database."""
import pytest
import sqlite3
from pathlib import Path

from app.storage.db import Database
from app.storage.repositories.provider_repo import ProviderRepository
from app.storage.repositories.credential_repo import CredentialRepository
from app.storage.repositories.model_repo import ModelRepository
from app.storage.repositories.test_run_repo import TestRunRepository
from app.storage.repositories.prompt_template_repo import PromptTemplateRepository
from app.models.provider import Provider
from app.models.credential import Credential
from app.models.model import Model, ModelCapability
from app.models.test_run import TestRun
from app.models.prompt_template import PromptTemplate


@pytest.fixture
def db():
    """In-memory SQLite database with migrations applied."""
    d = Database(db_path=":memory:")
    d.connect()
    yield d
    d.close()


@pytest.fixture
def conn(db):
    return db.connect()


class TestProviderRepository:
    def test_create_and_get(self, conn):
        repo = ProviderRepository(conn)
        p = repo.create(Provider(name="Test", slug="test", base_url="http://test.local"))
        assert p.id is not None
        fetched = repo.get_by_id(p.id)
        assert fetched.name == "Test"
        assert fetched.slug == "test"

    def test_list(self, conn):
        repo = ProviderRepository(conn)
        repo.create(Provider(name="A", slug="a"))
        repo.create(Provider(name="B", slug="b", active=False))
        all_providers = repo.list()
        assert len(all_providers) == 2
        active_only = repo.list(active_only=True)
        assert len(active_only) == 1

    def test_update(self, conn):
        repo = ProviderRepository(conn)
        p = repo.create(Provider(name="Old", slug="old"))
        p.name = "New"
        updated = repo.update(p)
        assert updated.name == "New"
        assert repo.get_by_id(p.id).name == "New"

    def test_delete(self, conn):
        repo = ProviderRepository(conn)
        p = repo.create(Provider(name="Del", slug="del"))
        assert repo.delete(p.id)
        assert repo.get_by_id(p.id) is None

    def test_get_by_slug(self, conn):
        repo = ProviderRepository(conn)
        repo.create(Provider(name="Slug Test", slug="slug-test"))
        assert repo.get_by_slug("slug-test") is not None
        assert repo.get_by_slug("nonexistent") is None


class TestCredentialRepository:
    def test_create_and_get(self, conn):
        p_repo = ProviderRepository(conn)
        provider = p_repo.create(Provider(name="P", slug="p"))
        repo = CredentialRepository(conn)
        c = repo.create(Credential(provider_id=provider.id, name="Cred", api_key="sk-test"))
        assert c.id is not None
        fetched = repo.get_by_id(c.id)
        assert fetched.name == "Cred"
        assert fetched.api_key == "sk-test"

    def test_list_by_provider(self, conn):
        p_repo = ProviderRepository(conn)
        p1 = p_repo.create(Provider(name="P1", slug="p1"))
        p2 = p_repo.create(Provider(name="P2", slug="p2"))
        repo = CredentialRepository(conn)
        repo.create(Credential(provider_id=p1.id, name="C1"))
        repo.create(Credential(provider_id=p2.id, name="C2"))
        assert len(repo.list(provider_id=p1.id)) == 1
        assert len(repo.list()) == 2


class TestModelRepository:
    def test_create_with_capabilities(self, conn):
        p_repo = ProviderRepository(conn)
        provider = p_repo.create(Provider(name="P", slug="p2"))
        repo = ModelRepository(conn)
        m = Model(provider_id=provider.id, technical_name="gpt-4o", display_name="GPT-4o",
                  capabilities=[ModelCapability(capability="chat"), ModelCapability(capability="vision")])
        created = repo.create(m)
        fetched = repo.get_by_id(created.id)
        caps = {c.capability for c in fetched.capabilities}
        assert "chat" in caps
        assert "vision" in caps

    def test_list_filters(self, conn):
        p_repo = ProviderRepository(conn)
        provider = p_repo.create(Provider(name="P", slug="p3"))
        repo = ModelRepository(conn)
        repo.create(Model(provider_id=provider.id, technical_name="text-m", type="text"))
        repo.create(Model(provider_id=provider.id, technical_name="img-m", type="image"))
        assert len(repo.list(type="text", active_only=False)) == 1
        assert len(repo.list(provider_id=provider.id, active_only=False)) == 2


class TestTestRunRepository:
    def test_create_and_list(self, conn):
        repo = TestRunRepository(conn)
        run = repo.create(TestRun(modality="text", params={"prompt": "hello"}, status="success"))
        assert run.id is not None
        runs = repo.list(limit=10)
        assert any(r.id == run.id for r in runs)

    def test_update_rating(self, conn):
        repo = TestRunRepository(conn)
        run = repo.create(TestRun(modality="text", status="success"))
        repo.update_rating(run.id, 5, "Excellent")
        fetched = repo.get_by_id(run.id)
        assert fetched.rating == 5
        assert fetched.rating_notes == "Excellent"


class TestPromptTemplateRepository:
    def test_create_and_list(self, conn):
        repo = PromptTemplateRepository(conn)
        t = repo.create(PromptTemplate(title="Test", content="Hello", modality="text"))
        fetched = repo.list(modality="text")
        assert any(x.id == t.id for x in fetched)
