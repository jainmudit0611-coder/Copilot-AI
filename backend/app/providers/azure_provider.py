from typing import List, Optional, Any
import httpx
import json
from app.providers.base import LLMProvider, EmbeddingProvider
from app.core.config import settings

class AzureOpenAILLMProvider(LLMProvider):
    def __init__(self):
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        self.api_version = settings.AZURE_OPENAI_API_VERSION

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> str:
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint or API key not configured")

        url = f"{self.endpoint.rstrip('/')}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Any] = None
    ) -> str:
        formatted_system = (system_prompt or "") + "\nRespond strictly in valid JSON format matching the schema."
        return await self.generate(prompt, system_prompt=formatted_system, temperature=0.1)

class AzureOpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        self.api_version = settings.AZURE_OPENAI_API_VERSION

    async def generate_embedding(self, text: str) -> List[float]:
        res = await self.generate_embeddings_batch([text])
        return res[0]

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OpenAI embedding configuration missing")

        url = f"{self.endpoint.rstrip('/')}/openai/deployments/{self.deployment}/embeddings?api-version={self.api_version}"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        
        payload = {"input": texts}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
