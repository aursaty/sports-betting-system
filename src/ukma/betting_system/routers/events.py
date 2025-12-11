from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ukma.betting_system.db import get_db
from ukma.betting_system.models import User, Event
from ukma.betting_system.schemas import EventCreate, EventUpdate, EventResponse
from ukma.betting_system.core import decode_access_token
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

router = APIRouter(prefix="/events", tags=["events"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to get the current authenticated user."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.email == payload["email"]))
    user = result.scalars().first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


@router.get("", response_model=list[EventResponse])
async def list_events(db: AsyncSession = Depends(get_db)):
    """Get all open betting events (public endpoint)."""
    result = await db.execute(select(Event).where(Event.status == "open"))
    events = result.scalars().all()
    return events


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new betting event (admin only)."""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create events"
        )
    
    # Create new event
    event = Event(
        title=event_data.title,
        team_a=event_data.team_a,
        team_b=event_data.team_b,
        odds_a=event_data.odds_a,
        odds_b=event_data.odds_b,
        status="open",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    return event


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific event by ID."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an event (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update events"
        )
    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update only provided fields
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    await db.commit()
    await db.refresh(event)
    
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an event (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete events"
        )
    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    await db.delete(event)
    await db.commit()
