import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ukma.betting_system.routers.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Lifespan called")
    yield


app = FastAPI(debug=True, title="peaky-betting-system", lifespan=lifespan)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
