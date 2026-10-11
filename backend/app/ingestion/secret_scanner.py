import re

SECRET_PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_ACCESS_KEY]'),
    (r'-----BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY-----[\s\S]+?-----END \1 KEY-----', '[REDACTED_PRIVATE_KEY]'),
    (r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', '[REDACTED_JWT_TOKEN]'),
    (r'postgres://[^:]+:[^@]+@[^/]+/[^\s]+', '[REDACTED_DB_URL]'),
    (r'(?i)(api_key|apikey|secret_key|secretkey|access_token|auth_token)\s*=\s*["\'][A-Za-z0-9_\-\.]{16,}["\']', '[REDACTED_API_KEY]'),
]

def scan_and_redact_secrets(content: str) -> str:
    redacted = content
    for pattern, replacement in SECRET_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted
