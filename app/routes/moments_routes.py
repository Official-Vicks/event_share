from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.services.moments_services import MomentService
from app.schemas.moments_schema import MomentBase, MomentResponse, MomentUpdate, MomentUpdateResponse
from app.schemas.user import GenericResponseModel
from db import get_db
from fastapi.security import OAuth2PasswordBearer
import uuid
from datetime import datetime
from app.services.user import UserService

router = APIRouter(prefix="/moments", tags=["Moments"])

@router.post("/create", response_model=GenericResponseModel[MomentResponse], status_code=status.HTTP_201_CREATED)
def create_moment(
    event_id: str = Form(...),
    content: str = Form(...),
    type: str = Form(...),
    media_file: Optional[UploadFile] = File(None),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login")),
    db: Session = Depends(get_db),
    request: Request = None
):
    moment_data = MomentBase(
        event_id=event_id,
        content=content,
        type=type
    )
    service = MomentService(db)
    user_service = UserService(db)
    user = user_service.get_current_user(token=token, db=db)
    response = service.create_moment(moment_data, user, token, media_file)
    if response["status_code"] != status.HTTP_201_CREATED:
        raise HTTPException(
            status_code=response["status_code"],
            detail=response["message"]
        )
    return GenericResponseModel[MomentResponse](
        status_code=response["status_code"],
        message=response["message"],
        data=response["data"]
    )

@router.get("/{event_id}/all", response_model=GenericResponseModel[List[MomentResponse]])
def get_moments_by_events(
    event_id: str,
    db: Session = Depends(get_db),
):
    service = MomentService(db)
    response = service.get_moments_by_event(uuid.UUID(event_id))
    if response["status_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response["status_code"],
            detail=response["message"]
        )
    return GenericResponseModel[List[MomentResponse]](
        status_code=response["status_code"],
        message=response["message"],
        data=response["data"]
    )

@router.put("/{id}/update", response_model=GenericResponseModel[MomentUpdateResponse])
def update_moment(
    id: uuid.UUID,
    content: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    media_file: Optional[UploadFile] = File(None),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login")),
    db: Session = Depends(get_db),
    request: Request = None
):
    moment_data = MomentUpdate(
        content=content,
        type=type
    )
    service = MomentService(db)
    user_service = UserService(db)
    user = user_service.get_current_user(token=token, db=db)
    response = service.update_moment(id, moment_data, user, token, media_file)
    if response["status_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response["status_code"],
            detail=response["message"]
        )
    return GenericResponseModel[MomentResponse](
        status_code=response["status_code"],
        message=response["message"],
        data=response["data"]
    )

@router.get("/mymoment/{id}", response_model=GenericResponseModel[MomentResponse])
def get_my_moment(
    id: str,
    db: Session = Depends(get_db),
    request: Request = None
):
    service = MomentService(db)
    user_service = UserService(db)
    user = user_service.get_current_user(db=db)
    response = service.get_moment_by_id(uuid.UUID(id))
    if response["status_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response["status_code"],
            detail=response["message"]
        )
    return GenericResponseModel[MomentResponse](
        status_code=response["status_code"],
        message=response["message"],
        data=response["data"]
    )

@router.delete("/{id}/delete", response_model=GenericResponseModel[None])
def delete_moment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login"))
):
    service = MomentService(db)
    user_service = UserService(db)
    user = user_service.get_current_user(token=token, db=db)
    response = service.delete_moment(id, user, token=token)
    if response["status_code"] != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response["status_code"],
            detail=response["message"]
        )
    return GenericResponseModel[None](
        status_code=response["status_code"],
        message=response["message"],
        data=None
    )