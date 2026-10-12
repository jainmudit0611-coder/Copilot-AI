from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base
from app.api import (
    auth,
    workspace,
    repository,
    chat,
    agent,
    bug,
    review,
    generator,
    evaluation,
    observability,
    github,
    health
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # In development mode, ensure demo user exists with valid hashed password
    if settings.APP_ENV == "development":
        import os
        from sqlalchemy import select
        from app.core.database import AsyncSessionLocal
        from app.models.user import User
        from app.core.security import hash_password

        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.email == "developer@codepilot.ai")
            res = await session.execute(stmt)
            demo_user = res.scalar_one_or_none()
            demo_password = os.getenv("DEMO_USER_PASSWORD", "Password123!")
            if not demo_user:
                demo_user = User(
                    email="developer@codepilot.ai",
                    name="Demo Engineer",
                    hashed_password=hash_password(demo_password),
                    role="DEVELOPER"
                )
                session.add(demo_user)
                await session.commit()
            elif demo_user.hashed_password == "hashed_demo_password":
                demo_user.hashed_password = hash_password(demo_password)
                await session.commit()
    yield
    # Cleanup on shutdown
    from app.core.redis import close_redis_client
    await close_redis_client()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Repository-Aware Agentic Software Engineering Copilot API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workspace.router, prefix="/api/v1")
app.include_router(repository.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
app.include_router(bug.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(generator.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")
app.include_router(observability.router, prefix="/api/v1")
app.include_router(github.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
