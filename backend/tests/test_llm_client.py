"""Tests for LLMClient."""
import json
from unittest.mock import patch, MagicMock
import pytest
from app.utils.llm_client import LLMClient


@pytest.fixture
def mock_providers():
    return [
        {
            "name": "test-provider",
            "api_key": "sk-test",
            "base_url": "https://api.test.com/v1",
            "model": "test-model",
        }
    ]


class TestLLMClientInit:
    def test_init_with_providers(self, mock_providers):
        with patch("app.utils.llm_client.OpenAI"):
            client = LLMClient(providers=mock_providers)
            assert len(client.providers) == 1
            assert client._active_provider is not None

    def test_init_filters_empty_keys(self):
        providers = [
            {"name": "valid", "api_key": "sk-ok", "base_url": "", "model": ""},
            {"name": "invalid", "api_key": "", "base_url": "", "model": ""},
        ]
        with patch("app.utils.llm_client.OpenAI"):
            client = LLMClient(providers=providers)
            available = client._get_available_providers()
            assert len(available) == 1
            assert available[0]["name"] == "valid"


class TestLLMClientChat:
    def test_chat_returns_stripped_content(self, mock_providers):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "  Hello World  "

        with patch("app.utils.llm_client.OpenAI") as mock_openai:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance

            client = LLMClient(providers=mock_providers)
            result = client.chat([{"role": "user", "content": "hi"}])
            assert result == "Hello World"

    def test_chat_strips_think_tags(self, mock_providers):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            "<think>Let me reason about this carefully...</think>The answer is 42"
        )

        with patch("app.utils.llm_client.OpenAI") as mock_openai:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance

            client = LLMClient(providers=mock_providers)
            result = client.chat([{"role": "user", "content": "think"}])
            assert "<think>" not in result
            assert "answer is 42" in result


class TestLLMClientChatJson:
    def test_chat_json_parses_response(self, mock_providers):
        expected = {"key": "value", "number": 123}
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(expected)

        with patch("app.utils.llm_client.OpenAI") as mock_openai:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance

            client = LLMClient(providers=mock_providers)
            result = client.chat_json([{"role": "user", "content": "json"}])
            assert result == expected

    def test_chat_json_strips_code_fences(self, mock_providers):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```json\n{\"a\": 1}\n```"

        with patch("app.utils.llm_client.OpenAI") as mock_openai:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance

            client = LLMClient(providers=mock_providers)
            result = client.chat_json([{"role": "user", "content": "json"}])
            assert result == {"a": 1}

    def test_chat_json_raises_on_invalid(self, mock_providers):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "not-json"

        with patch("app.utils.llm_client.OpenAI") as mock_openai:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance

            client = LLMClient(providers=mock_providers)
            with pytest.raises(ValueError, match="JSON格式无效"):
                client.chat_json([{"role": "user", "content": "json"}])
