from fastapi import APIRouter, Depends, Form, File, UploadFile, status
from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import Request
from app.services.event import EventService
from app.schemas.event_schema import EventUpdate, EventResponse, EventBase, EventUpdateResponse
from app.schemas.user import GenericResponseModel
from db import get_db
from fastapi.security import OAuth2PasswordBearer
import uuid
from datetime import datetime
router = APIRouter(prefix="/events", tags=["Events"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/create",response_model=GenericResponseModel[EventResponse],status_code=status.HTTP_201_CREATED)
def create_event(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    scheduled_at: datetime = Form(...),
    location: Optional[str] = Form(None),
    banner_file: Optional[UploadFile] = File(None),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None
):
    event_data = EventBase(
        name=name,
        description=description,
        scheduled_at=scheduled_at,
        location=location,
    )
    service = EventService(db)
    return service.create_event(event_data, token, banner_file, request)

@router.put(
    "/update/{event_id}",
    response_model=GenericResponseModel[EventResponse]
)
def update_event(
    event_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    scheduled_at: Optional[datetime] = Form(None),  # keep same type as create_event
    location: Optional[str] = Form(None),
    banner_file: Optional[UploadFile] = File(None),  # match service
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None
):
    event_data = EventUpdate(
        name=name,
        description=description,
        scheduled_at=scheduled_at,
        location=location,
    )
    service = EventService(db)
    return service.update_event(uuid.UUID(event_id), event_data, token, banner_file, request)

@router.get(
    "/{event_id}",
    response_model=GenericResponseModel[EventResponse]
)
def get_event(
    event_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    service = EventService(db)
    return service.get_single_event(uuid.UUID(event_id), token)

@router.get(
    "/event_manager/all",
    response_model=GenericResponseModel[List[EventResponse]]
)
def get_all_events(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    service = EventService(db)
    return service.get_events(token)

@router.delete(
    "/delete/{event_id}",
    response_model=GenericResponseModel[str]
)
def delete_event(
    event_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    service = EventService(db)
    return service.delete_event(event_id, token)

@router.delete(
    "/delete_all",
    response_model=GenericResponseModel[str]
)
def delete_all_events(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    service = EventService(db)
    return service.delete_all_events(token)