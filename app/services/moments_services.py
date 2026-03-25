from app.models.moments_models import Moment
from app.schemas.moments_schema import MomentBase, MomentResponse, MomentUpdate
from app.schemas.user import GenericResponseModel
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from uuid import UUID
from datetime import datetime
from app.models.event_models import Event, EventParticipant
from app.models.user_models import User
from app.utils.file_upload import save_file
from config import settings
import os, shutil, uuid

class MomentService():
    def __init__(self, db: Session):
        self.db = db

    def GenerateResponse(self, status_code: int, message: str, data: dict = None):
        return {
            "status_code": status_code,
            "message": message,
            "data": data
        }
    
    def create_moment(self, moment_data: MomentBase, user: User, token: str, media_file: UploadFile = None):
        event = self.db.query(Event).filter(Event.id == moment_data.event_id).first()
        joinedParticipant = self.db.query(EventParticipant).filter(EventParticipant.event_id == moment_data.event_id).first()
        if user.role != "participant":
            return self.GenerateResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Only participants can create moments."
            )
        if not event:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Event not found."
            )
        if not joinedParticipant or joinedParticipant.status != "joined":
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Join an event to create moments."
            )
        if moment_data.type in [ "image", "video"] and not media_file:
            return self.GenerateResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Media file is required for moment type '{moment_data.type}'."
            )
        if moment_data.type == "text" and media_file:
            return self.GenerateResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Media file should not be provided for moment type 'text'."
            )
        
        media_url = None
        if media_file:
            file_extension = os.path.splitext(media_file.filename)[1]
            if file_extension.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".avi"]:
                return self.GenerateResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Unsupported media file type."
                )

            upload_dir = os.path.join(settings.MOMENT_MEDIA_DIR, "moments")

            media_url = save_file(media_file, upload_dir)
            moment_data.media_url = media_url
        new_moment = Moment(
            id=uuid.uuid4(),
            event_id=moment_data.event_id,
            user_id=user.id,
            type=moment_data.type,
            content=moment_data.content,
            media_url=media_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(new_moment)
        self.db.commit()
        self.db.refresh(new_moment)
        return self.GenerateResponse(
            status_code=status.HTTP_201_CREATED,
            message="Moment created successfully.",
            data=MomentResponse.model_validate(new_moment)
        )

    def get_moments_by_event(self, event_id: UUID):
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Event not found."
            )
        moments = self.db.query(Moment).filter(Moment.event_id == event_id).all()
        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Moments retrieved successfully.",
            data=[MomentResponse.model_validate(moment) for moment in moments]
        )
    
    def update_moment(self, id: UUID, moment_data: MomentUpdate, user: User, token: str, media_file: UploadFile = None):
        moment = self.db.query(Moment).filter(Moment.id == id, Moment.user_id == user.id).first()
        if not moment:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Moment not found or you do not have permission to update it."
            )
        if moment_data.type and moment_data.type in ["image", "video"] and not media_file:
            return self.GenerateResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Media file is required for moment type '{moment_data.type}'."
            )
        if moment_data.type and moment_data.type == "text" and media_file:
            return self.GenerateResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Media file should not be provided for moment type 'text'."
            )
        
        if moment_data.content is not None:
            moment.content = moment_data.content
        if moment_data.type is not None:
            moment.type = moment_data.type
        moment.updated_at = datetime.utcnow()

        if media_file:
            file_extension = os.path.splitext(media_file.filename)[1]
            if file_extension.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".avi"]:
                return self.GenerateResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Unsupported media file type."
                )

            upload_dir = os.path.join(settings.MOMENT_MEDIA_DIR, "moments")

            moment.media_url = save_file(media_file, upload_dir)

        self.db.commit()
        self.db.refresh(moment)
        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Moment updated successfully.",
            data=MomentResponse.model_validate(moment)
        )

    def get_moment_by_id(self, id: UUID):
        moment = self.db.query(Moment).filter(Moment.id == id).first()
        if not moment:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Moment not found."
            )
        
        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Moment retrieved successfully.",
            data=MomentResponse.model_validate(moment)
        )

    def delete_moment(self, id:UUID, user: User, token: str):
        moment = self.db.query(Moment).filter(Moment.id == id, Moment.user_id == user.id).first()
        if not user:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found."
            )
        if not moment:
            return self.GenerateResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Moment not found or you do not have permission to delete it."
            )
        self.db.delete(moment)
        self.db.commit()
        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Moment deleted successfully."
        )