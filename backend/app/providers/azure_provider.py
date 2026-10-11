import logging
from typing import List, Optional, Any, Dict, Tuple
import httpx
from app.providers.base import LLMProvider, EmbeddingProvider
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

logger = logging.getLogger(__name__)


def _classify_and_raise_azure_error(status_code: int, response_text: str, deployment: str):
    """
    Classify HTTP error responses from Azure OpenAI and Azure AI Foundry into safe,
    typed exceptions without exposing credentials or internal tokens.
    """
    logger.warning("Azure AI call failed with status %d: %s", status_code, response_text[:200])
    if status_code == 401 or status_code == 403:
        raise AIAuthenticationError(
            "Azure AI authentication failed. Please verify AZURE_OPENAI_API_KEY and endpoint permissions."
        )
    elif status_code == 404:
        raise AIDeploymentNotFoundError(
            deployment,
            f"Azure AI deployment '{deployment}' not found. Please verify the deployed model name in Azure AI Foundry."
        )
    elif status_code == 429:
        raise AIRateLimitError(
            "Azure AI rate limit or quota exceeded. Please retry after some time."
        )
    elif status_code >= 500:
        raise AIServiceError(
            f"Azure AI service encountered an internal error ({status_code}). Please try again later."
        )
    else:
        # 400 or other bad request
        # Extract safe message if present
        err_msg = "Azure AI request rejected."
        try:
            import json
            data = json.loads(response_text)
            if "error" in data and isinstance(data["error"], dict):
                inner_msg = data["error"].get("message")
                if inner_msg:
                    err_msg = f"Azure AI request rejected: {inner_msg[:200]}"
        except Exception:
            pass
        raise AIServiceError(err_msg)


class AzureOpenAILLMProvider(LLMProvider):
    """
    Azure LLM Provider supporting:
    1. Microsoft Azure AI Foundry project endpoints (/api/projects/<project>/openai/v1/chat/completions)
    2. Microsoft Azure AI Foundry model inference endpoints (/models/chat/completions)
    3. Azure OpenAI Service endpoints (/openai/deployments/<deployment>/chat/completions)
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        self.endpoint = (endpoint if endpoint is not None else (settings.AZURE_OPENAI_ENDPOINT or "")).strip()
        self.api_key = (api_key if api_key is not None else (settings.AZURE_OPENAI_API_KEY or "")).strip()
        self.deployment = (deployment if deployment is not None else (settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4.1-mini")).strip()
        self.api_version = (api_version if api_version is not None else (settings.AZURE_OPENAI_API_VERSION or "2024-08-01-preview")).strip()

    def _validate_configuration(self):
        if not self.endpoint:
            raise AIConfigurationError(
                "AZURE_OPENAI_ENDPOINT is not configured. "
                "Provide a valid Azure OpenAI or Microsoft Foundry endpoint in .env."
            )
        if not self.api_key:
            raise AIConfigurationError(
                "AZURE_OPENAI_API_KEY is not configured. "
                "Provide your Azure AI API key in .env."
            )
        if not self.deployment:
            raise AIConfigurationError(
                "AZURE_OPENAI_DEPLOYMENT is not configured. "
                "Specify your deployed model name (e.g. gpt-4.1-mini)."
            )

    def _resolve_chat_endpoint_and_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        Detect endpoint type (Foundry project vs Model Inference vs Classic Azure OpenAI)
        and construct the proper URL and request payload.
        """
        raw_endpoint = self.endpoint.rstrip("/")
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Case 1: Azure AI Foundry Project endpoint
        # e.g., https://<res>.services.ai.azure.com/api/projects/<proj>[/openai/v1/responses or /openai/v1/chat/completions]
        if "/api/projects/" in raw_endpoint:
            base_project = raw_endpoint.split("/openai")[0].rstrip("/")
            url = f"{base_project}/openai/v1/chat/completions"
            payload: Dict[str, Any] = {
                "model": self.deployment,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if response_format:
                payload["response_format"] = response_format
            return url, headers, payload

        # Case 2: Azure AI Model Inference API (Foundry Serverless / models)
        # e.g., https://<res>.services.ai.azure.com/models
        if raw_endpoint.endswith("/models") or "services.ai.azure.com/models" in raw_endpoint:
            base_models = raw_endpoint if raw_endpoint.endswith("/models") else f"{raw_endpoint}/models"
            url = f"{base_models}/chat/completions?api-version=2024-05-01-preview"
            payload = {
                "model": self.deployment,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if response_format:
                payload["response_format"] = response_format
            return url, headers, payload

        # Case 3: Standard Azure OpenAI Resource endpoint
        # e.g., https://<res>.openai.azure.com/
        url = f"{raw_endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if response_format:
            payload["response_format"] = response_format
        return url, headers, payload

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> str:
        self._validate_configuration()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        url, headers, payload = self._resolve_chat_endpoint_and_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    _classify_and_raise_azure_error(resp.status_code, resp.text, self.deployment)
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            raise AITimeoutError(f"Azure AI request to deployment '{self.deployment}' timed out after 60s.")
        except httpx.ConnectError:
            raise AIServiceError("Unable to connect to Azure AI endpoint. Please verify endpoint network reachability.")
        except httpx.RequestError as exc:
            raise AIServiceError(f"Azure AI request failed: {type(exc).__name__}")

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Any] = None
    ) -> str:
        self._validate_configuration()

        formatted_system = (
            (system_prompt or "") +
            "\nYou must respond strictly with a valid JSON object matching the requested schema. Do not include markdown code block ticks unless strictly part of a JSON string."
        ).strip()

        messages = [
            {"role": "system", "content": formatted_system},
            {"role": "user", "content": prompt}
        ]

        url, headers, payload = self._resolve_chat_endpoint_and_payload(
            messages=messages,
            temperature=0.1,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    _classify_and_raise_azure_error(resp.status_code, resp.text, self.deployment)
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            raise AITimeoutError(f"Azure AI structured request to deployment '{self.deployment}' timed out after 60s.")
        except httpx.ConnectError:
            raise AIServiceError("Unable to connect to Azure AI endpoint. Please verify endpoint network reachability.")
        except httpx.RequestError as exc:
            raise AIServiceError(f"Azure AI structured request failed: {type(exc).__name__}")


class AzureOpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Azure Embedding Provider supporting:
    1. Standard Azure OpenAI embeddings deployment
    2. Explicit detection and clear reporting when an embedding model is missing on Foundry projects
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        self.endpoint = (endpoint if endpoint is not None else (settings.AZURE_OPENAI_ENDPOINT or "")).strip()
        self.api_key = (api_key if api_key is not None else (settings.AZURE_OPENAI_API_KEY or "")).strip()
        self.deployment = (deployment if deployment is not None else (settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT or "text-embedding-3-small")).strip()
        self.api_version = (api_version if api_version is not None else (settings.AZURE_OPENAI_API_VERSION or "2024-08-01-preview")).strip()

    def _validate_configuration(self):
        if not self.endpoint:
            raise AIConfigurationError("AZURE_OPENAI_ENDPOINT is not configured for embeddings.")
        if not self.api_key:
            raise AIConfigurationError("AZURE_OPENAI_API_KEY is not configured for embeddings.")
        if not self.deployment:
            raise AIConfigurationError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT is not configured.")

    def _resolve_embedding_endpoint_and_payload(self, texts: List[str]) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        raw_endpoint = self.endpoint.rstrip("/")
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Case 1: Microsoft Azure AI Foundry (services.ai.azure.com)
        # Foundry models inference endpoint for embeddings: /models/embeddings?api-version=2024-05-01-preview
        if "services.ai.azure.com" in raw_endpoint:
            from urllib.parse import urlparse
            parsed = urlparse(raw_endpoint if "://" in raw_endpoint else f"https://{raw_endpoint}")
            host = parsed.netloc or parsed.path.split("/")[0]
            url = f"https://{host}/models/embeddings?api-version=2024-05-01-preview"
            payload = {
                "model": self.deployment,
                "input": texts
            }
            return url, headers, payload

        # Case 2: Standard Azure OpenAI Resource (.openai.azure.com)
        url = f"{raw_endpoint}/openai/deployments/{self.deployment}/embeddings?api-version={self.api_version}"
        payload = {"input": texts}
        return url, headers, payload

    async def generate_embedding(self, text: str) -> List[float]:
        res = await self.generate_embeddings_batch([text])
        return res[0]

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        self._validate_configuration()
        url, headers, payload = self._resolve_embedding_endpoint_and_payload(texts)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 404:
                    raise AIDeploymentNotFoundError(
                        self.deployment,
                        f"Azure AI embedding deployment '{self.deployment}' not found. Please verify the deployed model name in Azure."
                    )
                if resp.status_code != 200:
                    _classify_and_raise_azure_error(resp.status_code, resp.text, self.deployment)
                data = resp.json()
                return [item["embedding"] for item in data["data"]]
        except (AIDeploymentNotFoundError, EmbeddingDeploymentMissingError, AIAuthenticationError, AIRateLimitError):
            raise
        except httpx.TimeoutException:
            raise AITimeoutError(f"Azure embedding request for '{self.deployment}' timed out after 30s.")
        except httpx.ConnectError:
            raise AIServiceError("Unable to connect to Azure AI embedding endpoint. Please check network connectivity.")
        except httpx.RequestError as exc:
            raise AIServiceError(f"Azure AI embedding request failed: {type(exc).__name__}")
