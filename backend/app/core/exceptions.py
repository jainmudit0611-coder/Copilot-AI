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
