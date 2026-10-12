from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.core.config import settings

is_sqlite = "sqlite" in settings.resolved_database_url
engine_kwargs = {
    "echo": False,
    "future": True,
}
if is_sqlite:
    engine_kwargs["poolclass"] = NullPool
    engine_kwargs["connect_args"] = {"timeout": 20}
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.resolved_database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
