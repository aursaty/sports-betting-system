from fastapi import APIRouter
import os
# from v1.users import users

router = APIRouter(prefix="/api/v1")


@router.get("/")
def root():
    return {"message": "Hello from FastAPI!"}


@router.get("/env")
def get_env():
    return dict(os.environ)
