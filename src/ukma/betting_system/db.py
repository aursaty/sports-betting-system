import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Master Database URL
DATABASE_URL_MASTER = os.getenv(
    "DATABASE_URL_MASTER",
    f"postgresql+asyncpg://{os.getenv('MASTER_DATABASE_USER', 'sports-betting-system-master-user')}:{os.getenv('MASTER_DATABASE_PASSWORD', '1528087d37efcf5b24f08ca0a3019677')}@database-master:5432/{os.getenv('DATABASE_NAME', 'sports-betting-system')}"
)

# Replica Database URL
DATABASE_URL_REPLICA = os.getenv(
    "DATABASE_URL_REPLICA",
    f"postgresql+asyncpg://{os.getenv('REPLICA_DATABASE_USER', 'sports-betting-system-replica-user')}:{os.getenv('REPLICA_DATABASE_PASSWORD', '4fb708f3ea0411d6d9672fbd6f1e7a66')}@database-replica-1:5432/{os.getenv('DATABASE_NAME', 'sports-betting-system')}"
)

# Create async engines
engine_master = create_async_engine(
    DATABASE_URL_MASTER,
    echo=False,
    future=True,
)

engine_replica = create_async_engine(
    DATABASE_URL_REPLICA,
    echo=False,
    future=True,
)

# Create async session factories
SessionLocalMaster = sessionmaker(
    engine_master, class_=AsyncSession, expire_on_commit=False
)

SessionLocalReplica = sessionmaker(
    engine_replica, class_=AsyncSession, expire_on_commit=False
)


async def get_db_master():
    """Dependency to get a master database session (Read/Write)."""
    async with SessionLocalMaster() as session:
        yield session


async def get_db_replica():
    """Dependency to get a replica database session (Read-Only)."""
    async with SessionLocalReplica() as session:
        yield session


async def get_db():
    """Default dependency (Master) for backward compatibility."""
    async with SessionLocalMaster() as session:
        yield session
