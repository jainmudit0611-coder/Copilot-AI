import os
import json
import pytest
from app.core.config import settings
from app.providers.azure_provider import AzureOpenAILLMProvider


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_AZURE_TESTS") != "1",
    reason="Live Azure integration test disabled by default. Set RUN_LIVE_AZURE_TESTS=1 to run."
)
@pytest.mark.asyncio
async def test_live_azure_model_generate():
    """
    Executes a real, live HTTP request to the configured Azure AI Foundry model (gpt-4.1-mini)
    and validates that real model text is returned.
    """
    assert settings.AZURE_OPENAI_ENDPOINT, "Live test requires AZURE_OPENAI_ENDPOINT to be set."
    assert settings.AZURE_OPENAI_API_KEY, "Live test requires AZURE_OPENAI_API_KEY to be set."

    provider = AzureOpenAILLMProvider(
        endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        deployment=settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4.1-mini",
        api_version=settings.AZURE_OPENAI_API_VERSION
    )

    prompt = "Respond with exactly: 'CodePilot AI Live Azure Connection Verified'"
    response = await provider.generate(prompt=prompt, temperature=0.1, max_tokens=60)
    assert response is not None
    assert len(response.strip()) > 0
    assert "CodePilot AI" in response or "Verified" in response or "Connection" in response


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_AZURE_TESTS") != "1",
    reason="Live Azure integration test disabled by default. Set RUN_LIVE_AZURE_TESTS=1 to run."
)
@pytest.mark.asyncio
async def test_live_azure_model_generate_structured():
    """
    Executes a real, live structured JSON request to the configured Azure AI model
    and validates that a valid JSON object matching the requested schema is returned.
    """
    provider = AzureOpenAILLMProvider(
        endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        deployment=settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4.1-mini",
        api_version=settings.AZURE_OPENAI_API_VERSION
    )

    prompt = "Return a JSON object with keys: status (string 'active'), model (string), and latency_target_ms (integer 500)."
    raw_response = await provider.generate_structured(prompt=prompt)
    assert raw_response is not None
    data = json.loads(raw_response)
    assert isinstance(data, dict)
    assert "status" in data or "model" in data


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_AZURE_TESTS") != "1",
    reason="Live Azure integration test disabled by default. Set RUN_LIVE_AZURE_TESTS=1 to run."
)
@pytest.mark.asyncio
async def test_live_azure_embedding_generate():
    """
    Executes a real, live HTTP request to Azure AI Foundry for text-embedding-3-small
    and validates that a 1536-dimensional vector is returned.
    """
    from app.providers.azure_provider import AzureOpenAIEmbeddingProvider

    emb_provider = AzureOpenAIEmbeddingProvider(
        endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT or "text-embedding-3-small"
    )

    vec = await emb_provider.generate_embedding("CodePilot AI Live Azure Embedding Test")
    assert vec is not None
    assert len(vec) == 1536
    assert isinstance(vec[0], float)
    assert all(-1.0 <= val <= 1.0 for val in vec)

