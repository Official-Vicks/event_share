from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid
from db import get_db
from app.services.user import UserService
from app.services.event import EventService
from app.models import User, ParticipationStatus
from fastapi.security import OAuth2PasswordBearer
from app.services.event_participation_service import (
    join_event_service,
    leave_event_service,
    set_participation_status,
    get_event_participants
)

router = APIRouter(prefix="/events", tags=["Event Participation"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# def getCurrentUser(db: Session = Depends(get_db)):
#     service = UserService(db)
#     global get_current_user
#     get_current_user = service.get_current_user(token=oauth2_scheme, db=db)


# join event
@router.post("/{event_id}/join")
def join_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    service = UserService(db)
    current_user = service.get_current_user(token, db)
    participant = join_event_service(db, current_user.id, event_id)

    return {
        "message": "Successfully joined event",
        "data": {
            "event_id": str(event_id),
            "status": participant.status
        }
    }

@router.post("/{event_id}/leave")
def leave_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    
    service = UserService(db)
    current_user = service.get_current_user(token, db)
    participant = leave_event_service(db, current_user.id, event_id)

    return {
        "message": "Successfully left event",
        "data": {
            "event_id": str(event_id),
            "status": participant.status
        }
    }

@router.patch("/{event_id}/status")
def update_participation_status(
    event_id: uuid.UUID,
    status: ParticipationStatus,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    
    service = UserService(db)
    current_user = service.get_current_user(token, db)
    participant = set_participation_status(
        db,
        current_user.id,
        event_id,
        status
    )

    return {
        "message": "Participation status updated",
        "data": {
            "event_id": str(event_id),
            "status": participant.status
        }
    }

@router.get("/{event_id}/participants")
def get_participants(
    event_id: uuid.UUID,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Only event managers are allowed to view event participants"""
    service = EventService(db)
    current_user = service.get_event_manager(token=token, db=db)
    participants = get_event_participants(db, current_user.id, event_id)

    return {
        "count": len(participants),
        "data": participants
    }