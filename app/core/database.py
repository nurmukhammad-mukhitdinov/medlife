from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import config

async_engine = create_async_engine(
    config.database.async_dsn,
    echo=False,
    pool_size=30,
    max_overflow=20,
    pool_timeout=60,
    pool_recycle=1800,
)

AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise


get_async_session = get_db
get_async_db = get_db
