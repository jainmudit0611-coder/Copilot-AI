from app.core.config import settings
from app.providers.base import LLMProvider, EmbeddingProvider
from app.providers.azure_provider import AzureOpenAILLMProvider, AzureOpenAIEmbeddingProvider
from app.providers.mock_provider import MockLLMProvider, MockEmbeddingProvider

def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "azure" and settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
        return AzureOpenAILLMProvider()
    return MockLLMProvider()

def get_embedding_provider() -> EmbeddingProvider:
    if settings.LLM_PROVIDER == "azure" and settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
        return AzureOpenAIEmbeddingProvider()
    return MockEmbeddingProvider()
