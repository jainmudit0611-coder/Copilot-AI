from app.core.config import settings
from app.core.exceptions import AIConfigurationError
from app.providers.base import LLMProvider, EmbeddingProvider
from app.providers.azure_provider import AzureOpenAILLMProvider, AzureOpenAIEmbeddingProvider
from app.providers.mock_provider import MockLLMProvider, MockEmbeddingProvider

def get_llm_provider() -> LLMProvider:
    """
    Centralized factory for LLM provider initialization.
    Strictly adheres to configured LLM_PROVIDER ('mock', 'azure', 'openai')
    without silent fallback when 'azure' mode is active.
    """
    provider = (settings.LLM_PROVIDER or "mock").strip().lower()

    if provider == "azure":
        return AzureOpenAILLMProvider()
    elif provider == "mock":
        return MockLLMProvider()
    elif provider == "openai":
        raise AIConfigurationError("Direct 'openai' provider is not configured. Use 'azure' or 'mock'.")
    else:
        raise AIConfigurationError(
            f"Unsupported LLM_PROVIDER '{provider}'. Supported options: 'mock', 'azure', 'openai'."
        )

def get_embedding_provider() -> EmbeddingProvider:
    """
    Centralized factory for Embedding provider initialization.
    Allows EMBEDDING_PROVIDER override (e.g. 'mock' embeddings while using 'azure' LLM).
    """
    provider = (settings.EMBEDDING_PROVIDER or settings.LLM_PROVIDER or "mock").strip().lower()

    if provider == "azure":
        return AzureOpenAIEmbeddingProvider()
    elif provider == "mock":
        return MockEmbeddingProvider()
    elif provider == "openai":
        raise AIConfigurationError("Direct 'openai' embedding provider is not configured.")
    else:
        raise AIConfigurationError(
            f"Unsupported embedding provider '{provider}'. Supported options: 'mock', 'azure'."
        )
