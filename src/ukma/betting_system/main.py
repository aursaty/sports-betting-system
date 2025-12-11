import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ukma.betting_system.db import engine_master
from ukma.betting_system.models import Base
from ukma.betting_system.routers import auth, events, bets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    async with engine_master.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/verified")
    yield
    print("Application shutdown")


app = FastAPI(
    debug=True,
    title="Sports Betting System API",
    description="Production-ready REST API for sports betting",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(bets.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# if __name__ == "__main__":
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8000,
#     )