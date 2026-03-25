from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid

from app.models import Event, EventParticipant, ParticipationStatus, User


def join_event_service(db: Session, user_id: uuid.UUID, event_id: uuid.UUID):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    participant = db.query(EventParticipant).filter(
        EventParticipant.user_id == user_id,
        EventParticipant.event_id == event_id
    ).first()

    if participant:
        if participant.status == ParticipationStatus.joined:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already joined this event"
            )

        # Update status (maybe → joined or left → joined)
        participant.status = ParticipationStatus.joined
    else:
        participant = EventParticipant(
            user_id=user_id,
            event_id=event_id,
            status=ParticipationStatus.joined
        )
        db.add(participant)

    db.commit()
    db.refresh(participant)

    return participant


def leave_event_service(db: Session, user_id: uuid.UUID, event_id: uuid.UUID):
    participant = db.query(EventParticipant).filter(
        EventParticipant.user_id == user_id,
        EventParticipant.event_id == event_id
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not part of this event"
        )

    if participant.status == ParticipationStatus.left:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already left this event"
        )
    
    if Event.organizer_id == user_id:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Organizer cannot leave their own event"
      )

    participant.status = ParticipationStatus.left

    db.commit()
    db.refresh(participant)

    return participant


def set_participation_status(
    db: Session,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
    new_status: ParticipationStatus
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    participant = db.query(EventParticipant).filter(
        EventParticipant.user_id == user_id,
        EventParticipant.event_id == event_id
    ).first()

    if participant:
        participant.status = new_status
    else:
        participant = EventParticipant(
            user_id=user_id,
            event_id=event_id,
            status=new_status
        )
        db.add(participant)

    db.commit()
    db.refresh(participant)

    return participant


def get_event_participants(db: Session, user_id: uuid.UUID, event_id: uuid.UUID):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    if event.organizer_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only event managers can view event participants")

    return db.query(EventParticipant).join(Event).filter(
        Event.organizer_id == user_id,
        EventParticipant.event_id == event_id,
        EventParticipant.status == ParticipationStatus.joined
    ).all()