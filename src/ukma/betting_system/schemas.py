from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Literal


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    team_a: str = Field(..., min_length=1, max_length=255)
    team_b: str = Field(..., min_length=1, max_length=255)
    odds_a: float = Field(..., gt=0)
    odds_b: float = Field(..., gt=0)


class EventUpdate(BaseModel):
    title: str | None = None
    team_a: str | None = None
    team_b: str | None = None
    odds_a: float | None = None
    odds_b: float | None = None
    status: Literal["open", "closed", "settled"] | None = None


class EventResponse(BaseModel):
    id: int
    title: str
    team_a: str
    team_b: str
    odds_a: float
    odds_b: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BetCreate(BaseModel):
    event_id: int
    amount: float = Field(..., gt=0)


class BetResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
