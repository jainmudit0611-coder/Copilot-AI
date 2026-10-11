import math
import hashlib
import json
from typing import List, Optional, Any
from app.providers.base import LLMProvider, EmbeddingProvider

class MockLLMProvider(LLMProvider):
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> str:
        prompt_lower = (prompt + " " + (system_prompt or "")).lower()
        if "auth" in prompt_lower or "login" in prompt_lower:
            return """Authentication flow analysis:
1. `src/auth/AuthProvider.ts`: Handles user authentication state, token storage in localStorage, and `/me` validation.
2. `backend/routes/auth_routes.py`: Implements user profile management and login endpoints.

Security note: `backend/routes/auth_routes.py:22` lacks proper authorization checks before modifying user profiles."""

        elif "order" in prompt_lower or "checkout" in prompt_lower:
            return """Order creation architecture:
1. `src/services/orderService.ts`: Sends order creation payload with idempotency key header.
2. `backend/routes/order_routes.py`: Receives order request and processes total calculation.

Notice: A potential race condition exists in idempotency processing at `backend/routes/order_routes.py:28`."""

        else:
            return """Codebase analysis summary:
The requested component interacts across the API routes, service layers, and core data models.

Referenced Files:
- `README.md:1-15`
- `src/services/orderService.ts:10-35`"""

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Any] = None
    ) -> str:
        combined_text = (prompt + " " + (system_prompt or "")).lower()
        
        if "reviewer" in combined_text or "code-review" in combined_text or "git diff" in combined_text or "code review" in combined_text:
            res = {
                "summary": "Code review identified 1 High severity security issue and 1 Medium performance issue.",
                "findings": [
                    {
                        "severity": "HIGH",
                        "category": "Security",
                        "file": "backend/routes/auth_routes.py",
                        "line": 22,
                        "description": "Missing ownership authorization check on profile update API.",
                        "evidence": "`update_user_profile` endpoint accepts `user_id` parameter directly without verifying caller identity.",
                        "recommendation": "Inject `current_user` dependency and ensure `current_user.id == user_id or current_user.role == 'admin'`.",
                        "confidence": 0.95
                    },
                    {
                        "severity": "MEDIUM",
                        "category": "Performance",
                        "file": "backend/routes/order_routes.py",
                        "line": 28,
                        "description": "Blocking `time.sleep` in async request handler.",
                        "evidence": "Use of synchronous `time.sleep` blocks the FastAPI event loop.",
                        "recommendation": "Replace `time.sleep` with `await asyncio.sleep`.",
                        "confidence": 0.90
                    }
                ]
            }
            return json.dumps(res)

        elif "bug" in combined_text or "error" in combined_text or "trace" in combined_text:
            res = {
                "error_summary": "Race condition in idempotency check causing duplicate orders.",
                "likely_root_cause": "The in-memory check for `x_idempotency_key` occurs prior to acquiring a database lock, leading to concurrent double execution under high throughput.",
                "evidence": "In `backend/routes/order_routes.py` lines 25-32, `time.sleep(0.05)` simulates asynchronous I/O between checking and inserting the key.",
                "suggested_fix": "Wrap the idempotency check in an atomic database lock or Redis distributed lock (e.g. `SETNX`).",
                "risk": "MEDIUM",
                "affected_files": ["backend/routes/order_routes.py", "src/services/orderService.ts"],
                "proposed_patch": """--- a/backend/routes/order_routes.py
+++ b/backend/routes/order_routes.py
@@ -25,5 +25,7 @@ async def create_order(payload: CreateOrderSchema):
-    if x_idempotency_key in PROCESSED_KEYS:
-        raise HTTPException(status_code=409)
+    async with redis_lock(f"lock:{x_idempotency_key}"):
+        if await redis.exists(x_idempotency_key):
+            raise HTTPException(status_code=409, detail="Duplicate order")
+        await redis.set(x_idempotency_key, "1", ex=3600)""",
                "tests_to_add": ["test_concurrent_order_creation_idempotency"]
            }
            return json.dumps(res)

        else:
            res = {
                "answer": "Repository analysis completed based on indexed symbol dependencies and AST structure.",
                "citations": [
                    {
                        "file": "src/auth/AuthProvider.ts",
                        "start_line": 1,
                        "end_line": 40,
                        "relevance": 0.92,
                        "snippet": "export const AuthProvider = ({ children }: { children: ReactNode }) => {"
                    },
                    {
                        "file": "backend/routes/order_routes.py",
                        "start_line": 20,
                        "end_line": 50,
                        "relevance": 0.88,
                        "snippet": "@router.post('')\nasync def create_order(payload: CreateOrderSchema):"
                    }
                ],
                "confidence": 0.91,
                "reasoning_summary": "Extracted AST symbols, matched vector similarity across 2 file chunks, and retrieved import call paths.",
                "limitations": []
            }
            return json.dumps(res)

class MockEmbeddingProvider(EmbeddingProvider):
    async def generate_embedding(self, text: str) -> List[float]:
        res = await self.generate_embeddings_batch([text])
        return res[0]

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            # Generate deterministic 1536-dim vector based on text hash
            h = hashlib.sha256(text.encode()).digest()
            vec = []
            for i in range(1536):
                val = (h[i % len(h)] + i) % 256
                vec.append(math.sin(val))
            # Normalize vector
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            embeddings.append([v / norm for v in vec])
        return embeddings
