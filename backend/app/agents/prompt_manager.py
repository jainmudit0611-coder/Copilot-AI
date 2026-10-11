from typing import Dict
from app.rag.prompts import (
    SYSTEM_REPOSITORY_CHAT_V1,
    SYSTEM_BUG_ANALYZER_V1,
    SYSTEM_CODE_REVIEW_V1,
    SYSTEM_TEST_GENERATOR_V1,
    SYSTEM_DOC_GENERATOR_V1
)

class PromptManager:
    _prompts: Dict[str, str] = {
        "repository_chat_v1": SYSTEM_REPOSITORY_CHAT_V1,
        "bug_analysis_v1": SYSTEM_BUG_ANALYZER_V1,
        "code_review_v1": SYSTEM_CODE_REVIEW_V1,
        "test_generation_v1": SYSTEM_TEST_GENERATOR_V1,
        "documentation_v1": SYSTEM_DOC_GENERATOR_V1
    }

    @classmethod
    def get_prompt(cls, key: str) -> str:
        return cls._prompts.get(key, SYSTEM_REPOSITORY_CHAT_V1)
