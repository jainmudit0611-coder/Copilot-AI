import re

INJECTION_PATTERNS = [
    r'(?i)ignore\s+all\s+previous\s+instructions',
    r'(?i)system\s+prompt\s+override',
    r'(?i)you\s+are\s+now\s+DAN',
    r'(?i)print\s+system\s+prompt'
]

class PromptInjectionGuard:
    @staticmethod
    def check_and_sanitize(user_input: str) -> str:
        sanitized = user_input
        for pattern in INJECTION_PATTERNS:
            sanitized = re.sub(pattern, '[BLOCKED_PROMPT_INJECTION_ATTEMPT]', sanitized)
        return sanitized
