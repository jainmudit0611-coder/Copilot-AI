# Security & Safety Architecture

## Security Controls
1. **Secret Scanning & Redaction**: Prior to vector chunking or LLM prompt assembly, code is scanned for API keys, AWS credentials, JWT secrets, private keys, and connection strings. Discovered secrets are masked (e.g. `[REDACTED_API_KEY]`).
2. **Prompt Injection Guard**: User inputs are sanitized to strip prompt injection delimiters and system prompt override attempts.
3. **ZIP Traversal Protection**: Uploaded ZIP files are checked against path traversal (`../`) and zip bomb attacks before decompression.
4. **GitHub Token Encryption**: OAuth & access tokens are stored in the database using Fernet symmetric encryption and decrypted only in memory during GitHub sync.
5. **Rate Limiting**: Token bucket algorithm enforced via Redis per user and workspace (`RATE_LIMIT_PER_MINUTE=60`).
