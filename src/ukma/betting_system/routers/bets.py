from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ukma.betting_system.db import get_db_master, get_db_replica
from ukma.betting_system.models import User, Bet, Event
from ukma.betting_system.schemas import BetCreate, BetResponse
from ukma.betting_system.core import decode_access_token

router = APIRouter(prefix="/bets", tags=["bets"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_replica)
) -> User:
    """Dependency to get the current authenticated user (Read-Only from Replica)."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(select(User).where(User.email == payload["email"]))
    user = result.scalars().first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


@router.post("", response_model=BetResponse, status_code=status.HTTP_201_CREATED)
async def place_bet(
    bet_data: BetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_master)
):
    """
    Place a bet securely preventing double spending.
    Uses DB transaction and row locking on the Master DB.
    """
    # Start transaction
    
    # 1. Lock the user row to prevent concurrent balance modifications
    # We must re-fetch the user from the Master DB with with_for_update()
    result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    user = result.scalars().first()
    
    if not user:
        # Should not happen if auth passed, but good safety
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check if event exists and is open
    event_result = await db.execute(select(Event).where(Event.id == bet_data.event_id))
    event = event_result.scalars().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.status != "open":
        raise HTTPException(status_code=400, detail="Event is not open for betting")

    # 3. Check balance
    if user.balance < bet_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds"
        )

    # 4. Deduct amount and create bet
    user.balance -= bet_data.amount
    
    bet = Bet(
        user_id=user.id,
        event_id=bet_data.event_id,
        amount=bet_data.amount,
        status="processed"
    )
    db.add(bet)
    
    # 5. Commit transaction
    await db.commit()
    await db.refresh(bet)
    
    return bet


@router.get("", response_model=list[BetResponse])
async def get_bets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_replica)
):
    """
    Get user's bet history.
    Reads from Replica DB to offload Master.
    """
    result = await db.execute(select(Bet).where(Bet.user_id == current_user.id))
    bets = result.scalars().all()
    return bets
