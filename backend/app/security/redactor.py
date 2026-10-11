from app.ingestion.secret_scanner import scan_and_redact_secrets

class PromptRedactor:
    @staticmethod
    def sanitize_prompt(prompt: str) -> str:
        return scan_and_redact_secrets(prompt)
