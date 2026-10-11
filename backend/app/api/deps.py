from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
import os
from app.core.security import decode_access_token, hash_password
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not token:
        # Development fallback user if unauthenticated
        stmt = select(User).where(User.email == "developer@codepilot.ai")
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        demo_password = os.getenv("DEMO_USER_PASSWORD", "Password123!")
        if not user:
            user = User(
                email="developer@codepilot.ai",
                name="Demo Engineer",
                hashed_password=hash_password(demo_password),
                role="DEVELOPER"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        elif user.hashed_password == "hashed_demo_password":
            user.hashed_password = hash_password(demo_password)
            await db.commit()
            await db.refresh(user)
        return user

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
