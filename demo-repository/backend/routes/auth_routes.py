from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

USERS_DB = {
    "usr_101": {"id": "usr_101", "name": "Alice Dev", "email": "alice@example.com", "role": "admin"}
}

@router.put("/users/{user_id}")
async def update_user_profile(user_id: str, payload: UserProfileUpdate):
    """
    Updates user profile information.
    INTENTIONAL SECURITY VULNERABILITY: Missing authorization check!
    Any caller can update any user profile without verifying their identity or authorization.
    """
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = USERS_DB[user_id]
    if payload.name:
        user["name"] = payload.name
    if payload.email:
        user["email"] = payload.email
        
    return {"status": "success", "user": user}
