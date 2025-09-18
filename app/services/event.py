import uuid, os, shutil
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from datetime import datetime
from app.models.event_models import Events
from app.services.user import UserService
from app.schemas.event_schema import EventUpdate, EventResponse, EventBase, EventUpdateResponse
from config import settings
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from typing import Optional
from fastapi.encoders import jsonable_encoder

class EventService:
    def __init__(self, db: Session):
        self.db = db

    def get_event_manager(self, token: str, db: Session):
        user_service = UserService(self.db)
        organizer = user_service.get_current_user(token=token, db=self.db)

        if organizer.role != "event_manager":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only event managers can create events."
            )
        return organizer
    
    def delete_file(self, file_url: str):
        """Delete a file from local storage based on its URL"""
        if not file_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found."
            )
        try:
            file_name = file_url.split("/")[-1]
            file_path = os.path.join(settings.MEDIA_DIR, "event_banners", file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # Optional: log the error instead of raising, so it doesn't break the update
            print(f"Error deleting file: {e}")


    def upload_file(self, banner_file: UploadFile = None, request: Request = None) -> Optional[str]:
        if banner_file:
            ext = banner_file.filename.split(".")[-1]
            file_name = f"{uuid.uuid4()}.{ext}"
            upload_dir = os.path.join(settings.MEDIA_DIR, "event_banners")
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, file_name)

            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(banner_file.file, buffer)

            if request:
                return str(request.base_url) + f"static/event_banners/{file_name}"
            else:
                return f"/static/event_banners/{file_name}"
        return None
    def GenerateResponse(self, status_code:int, message:str, data:Optional[dict] = None):
        return JSONResponse(
            status_code=status_code,
            content={
                "message": message,
                "data": data
            }
        )       
    def create_event(self, event_data: EventBase, token: str, banner_file: UploadFile = None, request: Request = None):
        organizer = self.get_event_manager(token=token, db=self.db)
        banner_url = None
        if banner_file:
            ext = banner_file.filename.split(".")[-1]
            file_name = f"{uuid.uuid4()}.{ext}"
            upload_dir = os.path.join(settings.MEDIA_DIR, "event_banners")
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, file_name)

            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(banner_file.file, buffer)

            if request:
                banner_url = str(request.base_url) + f"static/event_banners/{file_name}"
            else:
                banner_url = f"/static/event_banners/{file_name}"

        new_event = Events(
            id=uuid.uuid4(),
            name=event_data.name,
            description=event_data.description,
            scheduled_at=event_data.scheduled_at,
            location=event_data.location,
            organizer_id=organizer.id,
            banner_url=banner_url,
        )
        self.db.add(new_event)
        self.db.commit()
        self.db.refresh(new_event)

        return {
            "status_code": status.HTTP_201_CREATED,
            "message": "Event created successfully.",
            "data": EventResponse.from_orm(new_event)
        }

    def update_event(
        self,
        event_id: str,
        event_data: EventUpdate,
        token: str,
        banner_file: UploadFile = None,
        request: Request = None
    ):
        organizer = self.get_event_manager(token=token, db=self.db)
        event = (
            self.db.query(Events)
            .filter(Events.id == event_id, Events.organizer_id == organizer.id)
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found."
            )

        # Update fields if provided
        if event_data.name is not None:
            event.name = event_data.name
        if event_data.description is not None:
            event.description = event_data.description
        if event_data.scheduled_at is not None:
            event.scheduled_at = event_data.scheduled_at
        if event_data.location is not None:
            event.location = event_data.location

        # Handle banner file update
        if banner_file:
            if event.banner_url:
                self.delete_file(event.banner_url)
            event.banner_url = self.upload_file(banner_file=banner_file, request=request)

        self.db.commit()
        self.db.refresh(event)

        return {
            "status_code": status.HTTP_200_OK,
            "message": "Event updated successfully.",
            "data": EventResponse.from_orm(event)
        }

    def get_single_event(self, event_id: str, token: str):
        organizer = self.get_event_manager(token=token, db=self.db)
        event = (
            self.db.query(Events)
            .filter(Events.id == event_id, Events.organizer_id == organizer.id)
            .first()
        )

        if not event:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Event not found."
            )

        event_data = EventResponse.from_orm(event)

        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Event retrieved successfully.",
            data=jsonable_encoder(event_data)
        )

    def get_events(self, token: str):
        organizer = self.get_event_manager(token=token, db=self.db)
        events = (
            self.db.query(Events)
            .filter(Events.organizer_id == organizer.id)
            .all()
        )

        if not events:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="No events found."
            )

        events_data = [EventResponse.from_orm(event) for event in events]
        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Events retrieved successfully.",
            data=jsonable_encoder(events_data)
        )
    
    def delete_event(self, event_id: str, token: str):
        organizer = self.get_event_manager(token=token, db=self.db)
        event = (
            self.db.query(Events)
            .filter(Events.id == event_id, Events.organizer_id == organizer.id)
            .first()
        )

        if not event:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Event not found."
            )
        if event.banner_url:
            self.delete_file(event.banner_url)
        self.db.delete(event)
        self.db.commit()

        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Event deleted successfully."
        )
    
    def delete_all_events(self, token: str):
        organizer = self.get_event_manager(token=token, db=self.db)
        events = (
            self.db.query(Events)
            .filter(Events.organizer_id == organizer.id)
            .all()
        )

        if not events:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="No events found to delete."
            )
        for event in events:
            if event.banner_url:
                self.delete_file(event.banner_url)
            self.db.delete(event)
        self.db.commit()
        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="All events deleted successfully."
        )