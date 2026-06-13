from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from db_models import Base
from logger import get_logger


logger = get_logger(__name__)


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def init_database() -> None:
    """
    Create database tables for the demo.
    """
    logger.info("Initialising database tables")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    logger.info("Database tables initialised")


async def close_database() -> None:
    """
    Close database connection pool on application shutdown.
    """
    await engine.dispose()
    logger.info("Database engine disposed")


async def get_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency for request-scoped database sessions.
    """
    async with AsyncSessionLocal() as session:
        yield session