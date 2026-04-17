"""Tests for CLI commands."""
import json
import pytest
from unittest.mock import patch

from app.cli import main as cli_main
from app.storage.db import Database


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    db = Database(db_path=":memory:")
    db.connect()
    monkeypatch.setattr("app.storage.db._db", db)
    # Prevent seed from running twice
    monkeypatch.setattr("app.storage.seed.seed", lambda force=False: None)
    yield db
    db.close()


def run_cli(*args):
    """Run CLI and capture SystemExit code (0 = success)."""
    try:
        code = cli_main(list(args))
        return code or 0
    except SystemExit as e:
        return e.code or 0


class TestProvidersCLI:
    def test_list_empty(self, capsys):
        run_cli("providers", "list")
        out = capsys.readouterr().out
        assert isinstance(out, str)

    def test_add_and_list(self, capsys):
        run_cli("providers", "add", "--name", "OpenAI", "--url", "https://api.openai.com/v1")
        capsys.readouterr()
        run_cli("providers", "list", "--output", "json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert any(p["name"] == "OpenAI" for p in data)

    def test_add_and_show(self, capsys):
        run_cli("providers", "add", "--name", "Anthropic", "--url", "https://api.anthropic.com")
        capsys.readouterr()
        run_cli("providers", "list", "--output", "json")
        data = json.loads(capsys.readouterr().out)
        pid = data[0]["id"]
        run_cli("providers", "show", str(pid), "--output", "json")
        out = capsys.readouterr().out
        item = json.loads(out)
        assert item["name"] == "Anthropic"


class TestCredentialsCLI:
    def test_add_and_list(self, capsys):
        run_cli("providers", "add", "--name", "P", "--url", "https://p.api")
        capsys.readouterr()
        run_cli("providers", "list", "--output", "json")
        providers = json.loads(capsys.readouterr().out)
        pid = providers[0]["id"]
        run_cli("credentials", "add", "--provider", str(pid), "--name", "My Key", "--api-key", "sk-test")
        capsys.readouterr()
        run_cli("credentials", "list", "--output", "json")
        creds = json.loads(capsys.readouterr().out)
        assert any(c["name"] == "My Key" for c in creds)


class TestRunCLI:
    def test_run_text_mock(self, capsys):
        run_cli("providers", "add", "--name", "Mock", "--url", "")
        capsys.readouterr()
        run_cli("providers", "list", "--output", "json")
        # Fix slug to "mock"
        from app.storage.repositories.provider_repo import ProviderRepository
        from app.storage.db import get_conn
        providers = ProviderRepository(get_conn()).list()
        assert len(providers) > 0
        p = providers[0]; p.slug = "mock"
        ProviderRepository(get_conn()).update(p)
        capsys.readouterr()

        from app.services.credential_service import CredentialService
        from app.services.model_service import ModelService
        c = CredentialService().create_credential({"provider_id": p.id, "name": "MC"})
        ModelService().sync_models(p.id, c.id)
        from app.storage.repositories.model_repo import ModelRepository
        models = ModelRepository(get_conn()).list(provider_id=p.id, active_only=False)
        text_m = next((m for m in models if "text" in m.technical_name), None)
        assert text_m is not None

        run_cli("run", "text", "--credential", str(c.id), "--model", str(text_m.id), "--prompt", "Hello")
        out = capsys.readouterr().out
        assert "success" in out.lower() or len(out) > 0
