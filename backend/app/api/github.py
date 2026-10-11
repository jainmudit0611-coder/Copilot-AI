import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.api.deps import get_current_user
from app.models.user import User
from app.core.security import decrypt_secret

router = APIRouter(prefix="/github", tags=["GitHub Integration"])

@router.get("/repositories")
async def list_github_repositories(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    token = decrypt_secret(current_user.github_token) if current_user.github_token else None
    
    if not token:
        # Fallback realistic repositories list for development / demonstration
        return [
          {
            "id": 101,
            "name": "demo-ecommerce-app",
            "full_name": "codepilot-demo/demo-ecommerce-app",
            "description": "Full-stack E-Commerce app with FastAPI backend & React frontend",
            "html_url": "https://github.com/codepilot-demo/demo-ecommerce-app",
            "default_branch": "main",
            "language": "TypeScript"
          },
          {
            "id": 102,
            "name": "payment-gateway-service",
            "full_name": "codepilot-demo/payment-gateway-service",
            "description": "Microservice handling Stripe & PayPal payment webhooks",
            "html_url": "https://github.com/codepilot-demo/payment-gateway-service",
            "default_branch": "main",
            "language": "Python"
          }
        ]

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get("https://api.github.com/user/repos?sort=updated&per_page=30", headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch GitHub repositories")
        repos = resp.json()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r["description"],
                "html_url": r["html_url"],
                "default_branch": r["default_branch"],
                "language": r["language"]
            }
            for r in repos
        ]

@router.get("/repositories/{owner}/{repo}/branches")
async def list_repository_branches(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    return [
        {"name": "main", "commit": {"sha": "a1b2c3d4e5"}},
        {"name": "develop", "commit": {"sha": "f6g7h8i9j0"}},
        {"name": "feature/idempotency-fix", "commit": {"sha": "1a2b3c4d5e"}}
    ]

@router.get("/repositories/{owner}/{repo}/pulls")
async def list_repository_pull_requests(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    return [
        {
            "id": 1,
            "number": 42,
            "title": "Fix duplicate order creation race condition in order_routes.py",
            "state": "open",
            "user": "dev-engineer",
            "created_at": "2026-10-08T10:00:00Z"
        }
    ]

@router.get("/repositories/{owner}/{repo}/pulls/{pr_number}/diff")
async def get_pull_request_diff(
    owner: str,
    repo: str,
    pr_number: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    diff_content = """--- a/backend/routes/order_routes.py
+++ b/backend/routes/order_routes.py
@@ -25,6 +25,8 @@ async def create_order(payload: CreateOrderSchema):
-    if x_idempotency_key in PROCESSED_KEYS:
-        raise HTTPException(status_code=409)
+    async with redis_lock(f"lock:{x_idempotency_key}"):
+        if await redis.exists(x_idempotency_key):
+            raise HTTPException(status_code=409, detail="Duplicate order")"""
    return {"pr_number": pr_number, "diff": diff_content}
