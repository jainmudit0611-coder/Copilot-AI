from typing import Optional
from fastapi import HTTPException, status

class CodePilotException(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})

class RepositoryNotIndexedException(CodePilotException):
    def __init__(self, repo_id: str):
        super().__init__(
            code="REPOSITORY_NOT_INDEXED",
            message=f"Repository '{repo_id}' is not yet indexed. Please trigger indexing first.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class UnauthorizedAccessException(CodePilotException):
    def __init__(self, detail: str = "Insufficient permissions for this workspace/repository"):
        super().__init__(
            code="UNAUTHORIZED_ACCESS",
            message=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )

class AgentExecutionException(CodePilotException):
    def __init__(self, reason: str):
        super().__init__(
            code="AGENT_EXECUTION_FAILED",
            message=f"Agent execution encountered an error: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class AIProviderException(CodePilotException):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(code=code, message=message, status_code=status_code)

class AIConfigurationError(AIProviderException):
    def __init__(self, message: str):
        super().__init__(
            code="AI_CONFIGURATION_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class AIAuthenticationError(AIProviderException):
    def __init__(self, message: str = "Azure AI authentication failed. Please verify API key or credential configuration."):
        super().__init__(
            code="AI_AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AIDeploymentNotFoundError(AIProviderException):
    def __init__(self, deployment_name: str, message: Optional[str] = None):
        msg = message or f"Azure AI deployment '{deployment_name}' was not found. Please verify the deployed model name in Azure AI Foundry."
        super().__init__(
            code="AI_DEPLOYMENT_NOT_FOUND",
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND
        )

class AIRateLimitError(AIProviderException):
    def __init__(self, message: str = "Azure AI rate limit or quota exceeded. Please retry after some time."):
        super().__init__(
            code="AI_RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class AITimeoutError(AIProviderException):
    def __init__(self, message: str = "Azure AI request timed out."):
        super().__init__(
            code="AI_TIMEOUT",
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT
        )

class AIServiceError(AIProviderException):
    def __init__(self, message: str = "Azure AI service returned an error."):
        super().__init__(
            code="AI_SERVICE_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY
        )

class EmbeddingDeploymentMissingError(AIProviderException):
    def __init__(self, deployment_name: str):
        super().__init__(
            code="EMBEDDING_DEPLOYMENT_MISSING",
            message=(
                f"Azure embedding deployment '{deployment_name}' is not configured or not deployed. "
                "Chat models (like gpt-4.1-mini) cannot generate embeddings. "
                "Please deploy 'text-embedding-3-small' in Azure AI Foundry or use mock mode for local tests."
            ),
            status_code=status.HTTP_400_BAD_REQUEST
        )
