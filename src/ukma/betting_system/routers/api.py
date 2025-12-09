from fastapi import APIRouter
from v1.users import users

router = APIRouter(prefix="/api/v1")


@router.get("/")
def root():
    return {"message": "Hello from FastAPI!"}
