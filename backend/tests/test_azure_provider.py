import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.config import settings
from app.core.exceptions import (
    AIConfigurationError,
    AIAuthenticationError,
    AIDeploymentNotFoundError,
    AIRateLimitError,
    AITimeoutError,
    AIServiceError,
    EmbeddingDeploymentMissingError,
)
from app.providers.factory import get_llm_provider, get_embedding_provider
from app.providers.azure_provider import AzureOpenAILLMProvider, AzureOpenAIEmbeddingProvider
from app.providers.mock_provider import MockLLMProvider, MockEmbeddingProvider


def test_provider_selection_mock(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "mock")
    llm = get_llm_provider()
    emb = get_embedding_provider()
    assert isinstance(llm, MockLLMProvider)
    assert isinstance(emb, MockEmbeddingProvider)


def test_provider_selection_azure(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "azure")
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "azure")
    monkeypatch.setattr(settings, "AZURE_OPENAI_ENDPOINT", "https://test-resource.services.ai.azure.com/api/projects/proj-1")
    monkeypatch.setattr(settings, "AZURE_OPENAI_API_KEY", "test-key-mock")
    monkeypatch.setattr(settings, "AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

    llm = get_llm_provider()
    emb = get_embedding_provider()
    assert isinstance(llm, AzureOpenAILLMProvider)
    assert isinstance(emb, AzureOpenAIEmbeddingProvider)


def test_provider_selection_unsupported(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "invalid_provider")
    with pytest.raises(AIConfigurationError) as exc_info:
        get_llm_provider()
    assert "Unsupported LLM_PROVIDER" in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_azure_missing_configuration_validation():
    provider = AzureOpenAILLMProvider(endpoint="", api_key="", deployment="")
    with pytest.raises(AIConfigurationError) as exc:
        await provider.generate("Hello")
    assert "AZURE_OPENAI_ENDPOINT is not configured" in exc.value.detail["message"]


def test_azure_url_resolution_foundry_project():
    provider = AzureOpenAILLMProvider(
        endpoint="https://mudit-res.services.ai.azure.com/api/projects/my-project/openai/v1/responses",
        api_key="dummy-key",
        deployment="gpt-4.1-mini"
    )
    url, headers, payload = provider._resolve_chat_endpoint_and_payload(
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.2,
        max_tokens=100
    )
    assert url == "https://mudit-res.services.ai.azure.com/api/projects/my-project/openai/v1/chat/completions"
    assert headers["api-key"] == "dummy-key"
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["messages"] == [{"role": "user", "content": "hi"}]


def test_azure_url_resolution_classic_azure_openai():
    provider = AzureOpenAILLMProvider(
        endpoint="https://my-aoai-instance.openai.azure.com/",
        api_key="dummy-key",
        deployment="gpt-4o",
        api_version="2024-08-01-preview"
    )
    url, headers, payload = provider._resolve_chat_endpoint_and_payload(
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.2,
        max_tokens=100
    )
    assert url == "https://my-aoai-instance.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
    assert headers["api-key"] == "dummy-key"
    assert "model" not in payload


@pytest.mark.asyncio
async def test_azure_successful_model_response():
    provider = AzureOpenAILLMProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="dummy-key",
        deployment="gpt-4.1-mini"
    )
    fake_response = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": "Azure Foundry generated response successfully."}}]},
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        res = await provider.generate("Test prompt")
        assert res == "Azure Foundry generated response successfully."


@pytest.mark.asyncio
async def test_azure_structured_model_response():
    provider = AzureOpenAILLMProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="dummy-key",
        deployment="gpt-4.1-mini"
    )
    fake_json_content = json.dumps({"answer": "Structured answer", "confidence": 0.95})
    fake_response = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": fake_json_content}}]},
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        res = await provider.generate_structured("Explain auth flow")
        data = json.loads(res)
        assert data["answer"] == "Structured answer"
        assert data["confidence"] == 0.95


@pytest.mark.asyncio
async def test_azure_authentication_error_401():
    provider = AzureOpenAILLMProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="invalid-key",
        deployment="gpt-4.1-mini"
    )
    fake_response = httpx.Response(
        status_code=401,
        text='{"error":{"code":"401","message":"Access denied due to invalid subscription key."}}',
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        with pytest.raises(AIAuthenticationError) as exc:
            await provider.generate("Hello")
        assert "authentication failed" in exc.value.detail["message"]
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_azure_deployment_not_found_404():
    provider = AzureOpenAILLMProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="valid-key",
        deployment="nonexistent-model"
    )
    fake_response = httpx.Response(
        status_code=404,
        text='{"error":{"code":"DeploymentNotFound","message":"The API deployment does not exist."}}',
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        with pytest.raises(AIDeploymentNotFoundError) as exc:
            await provider.generate("Hello")
        assert "nonexistent-model" in exc.value.detail["message"]
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_azure_rate_limit_429():
    provider = AzureOpenAILLMProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="valid-key",
        deployment="gpt-4.1-mini"
    )
    fake_response = httpx.Response(
        status_code=429,
        text='{"error":{"code":"429","message":"Requests rate limit exceeded."}}',
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        with pytest.raises(AIRateLimitError) as exc:
            await provider.generate("Hello")
        assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_azure_timeout_error():
    provider = AzureOpenAILLMProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="valid-key",
        deployment="gpt-4.1-mini"
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")
        with pytest.raises(AITimeoutError) as exc:
            await provider.generate("Hello")
        assert exc.value.status_code == 504


def test_azure_embedding_url_resolution_foundry():
    provider = AzureOpenAIEmbeddingProvider(
        endpoint="https://mudit-res.services.ai.azure.com/api/projects/my-project",
        api_key="dummy-key",
        deployment="text-embedding-3-small"
    )
    url, headers, payload = provider._resolve_embedding_endpoint_and_payload(["hello world"])
    assert url == "https://mudit-res.services.ai.azure.com/models/embeddings?api-version=2024-05-01-preview"
    assert headers["api-key"] == "dummy-key"
    assert payload["model"] == "text-embedding-3-small"
    assert payload["input"] == ["hello world"]


def test_azure_embedding_url_resolution_classic():
    provider = AzureOpenAIEmbeddingProvider(
        endpoint="https://my-aoai.openai.azure.com/",
        api_key="dummy-key",
        deployment="text-embedding-3-small",
        api_version="2024-08-01-preview"
    )
    url, headers, payload = provider._resolve_embedding_endpoint_and_payload(["hello world"])
    assert url == "https://my-aoai.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-08-01-preview"
    assert headers["api-key"] == "dummy-key"
    assert "model" not in payload


@pytest.mark.asyncio
async def test_azure_embedding_successful_response():
    provider = AzureOpenAIEmbeddingProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="dummy-key",
        deployment="text-embedding-3-small"
    )
    fake_vec = [0.01] * 1536
    fake_response = httpx.Response(
        status_code=200,
        json={"data": [{"embedding": fake_vec}]},
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        vec = await provider.generate_embedding("Test sentence")
        assert len(vec) == 1536
        assert vec[0] == 0.01


@pytest.mark.asyncio
async def test_azure_embedding_authentication_error():
    provider = AzureOpenAIEmbeddingProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="bad-key",
        deployment="text-embedding-3-small"
    )
    fake_response = httpx.Response(
        status_code=401,
        text='{"error":{"code":"401","message":"Invalid subscription key."}}',
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        with pytest.raises(AIAuthenticationError):
            await provider.generate_embedding("Test sentence")


@pytest.mark.asyncio
async def test_azure_embedding_deployment_not_found():
    provider = AzureOpenAIEmbeddingProvider(
        endpoint="https://my-res.services.ai.azure.com/api/projects/test-proj",
        api_key="valid-key",
        deployment="missing-emb-deployment"
    )
    fake_response = httpx.Response(
        status_code=404,
        text='{"error":{"code":"DeploymentNotFound","message":"Model not found"}}',
        request=httpx.Request("POST", "http://test")
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        with pytest.raises(AIDeploymentNotFoundError) as exc:
            await provider.generate_embedding("Test sentence")
        assert "missing-emb-deployment" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_mock_embedding_dimensions_and_normalization():
    mock_emb = MockEmbeddingProvider()
    vec = await mock_emb.generate_embedding("def calculate_total(x): return x * 1.1")
    assert len(vec) == 1536
    # Verify unit-vector normalization
    import math
    norm = math.sqrt(sum(v * v for v in vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-4)

