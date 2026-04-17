"""Tests for provider adapters with mocked HTTP responses."""
import pytest
from unittest.mock import patch, MagicMock

from app.models.credential import Credential
from app.providers.mock import MockProvider
from app.providers.openai_compat import OpenAICompatProvider


class TestMockProvider:
    def test_test_connection(self):
        provider = MockProvider(latency_ms=0)
        cred = Credential()
        result = provider.test_connection(cred)
        assert result.success is True

    def test_list_models(self):
        provider = MockProvider(latency_ms=0)
        models = provider.list_models(Credential())
        assert len(models) == 3
        names = {m["technical_name"] for m in models}
        assert "mock-text-v1" in names
        assert "mock-image-v1" in names

    def test_run_text(self):
        provider = MockProvider(latency_ms=0)
        result = provider.run_text(Credential(), "mock-text-v1", {"user_prompt": "hello"})
        assert result.success is True
        assert len(result.content) > 0

    def test_run_image(self):
        provider = MockProvider(latency_ms=0)
        result = provider.run_image(Credential(), "mock-image-v1", {"prompt": "cat"})
        assert result.success is True
        assert len(result.urls) > 0

    def test_run_audio(self):
        provider = MockProvider(latency_ms=0)
        result = provider.run_audio(Credential(), "mock-audio-v1", {"operation": "transcription"})
        assert result.success is True
        assert len(result.transcript) > 0

    def test_streaming(self):
        provider = MockProvider(latency_ms=0)
        chunks = []
        result = provider.run_text(Credential(), "mock-text-v1", {},
                                   on_chunk=lambda c: chunks.append(c))
        assert len(chunks) > 0


class TestOpenAICompatProvider:
    def test_run_text_success(self):
        provider = OpenAICompatProvider(base_url="https://api.example.com")
        cred = Credential(api_key="sk-test")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hello from mock"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }
        with patch.object(provider._http, "post", return_value=mock_resp):
            result = provider.run_text(cred, "gpt-4o", {"user_prompt": "Hello"})
        assert result.success is True
        assert result.content == "Hello from mock"
        assert result.total_tokens == 15

    def test_run_text_http_error(self):
        provider = OpenAICompatProvider(base_url="https://api.example.com")
        cred = Credential(api_key="sk-test")
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        with patch.object(provider._http, "post", return_value=mock_resp):
            result = provider.run_text(cred, "gpt-4o", {"user_prompt": "Hello"})
        assert result.success is False
        assert "401" in result.error

    def test_list_models(self):
        provider = OpenAICompatProvider(base_url="https://api.example.com")
        cred = Credential(api_key="sk-test")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"id": "gpt-4"}, {"id": "gpt-3.5-turbo"}]}
        with patch.object(provider._http, "get", return_value=mock_resp):
            models = provider.list_models(cred)
        assert len(models) == 2
        assert models[0]["technical_name"] == "gpt-4"
