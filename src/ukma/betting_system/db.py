import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database URL - Use environment variable or construct from individual vars
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{os.getenv('MASTER_DATABASE_USER', 'postgres')}:{os.getenv('MASTER_DATABASE_PASSWORD', 'postgres')}@database-master:5432/{os.getenv('DATABASE_NAME', 'betting_system')}"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """Dependency to get a database session."""
    async with async_session_maker() as session:
        yield session
