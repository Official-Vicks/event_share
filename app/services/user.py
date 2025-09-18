from db import get_db
from db import SessionLocal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from config import settings
from app.models.user_models import User, BlacklistedToken
from jwt import (create_access_token, create_refresh_token,
                 decode_access_token, decode_refresh_token,
                 is_token_blacklisted, blacklist_token)
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from app.schemas.user import UserRegister, ProfileModel, AuthResponse, UserLogin, RefreshTokenRequest, ProfileResponseWrapper, ProfileResponse
from uuid import uuid4
import uuid
import shutil
import os
from fastapi import UploadFile
from security import hash_password, verify_password
from app.schemas.admin import AdminRegister, AdminLogin, AdminProfileModel, AdminAuthResponse, AdminGetUserProfileOut
from fastapi.encoders import jsonable_encoder

class UserService:
    def __init__(self, db:Session = SessionLocal()):
        self.db = db

    def GenerateResponse(self, status_code:int, message:str, data:Optional[dict] = None):
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder({
                "message": message,
                "data": data
            })
        )
    def get_current_user(self, token: str, db: Session):
        payload = decode_access_token(token, db)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials."
            )

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        return user

    def get_user_profile(self, token: str, db: Session):
        current_user = self.get_current_user(token=token, db=db)

        if current_user.role == "admin":
            return self.GenerateResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Admins are not allowed to access this resource",
                data=None
            )

        profile_data = ProfileResponse.from_orm(current_user).dict()

        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Profile fetched successfully!",
            data=profile_data
        )
    
    def register_user(self, user_data: UserRegister):
        existing_user = self.db.query(User).filter_by(email=user_data.email).first()
        existing_username = self.db.query(User).filter_by(username=user_data.username).first()
        if existing_username:
            return self.GenerateResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Username already taken."
            )
        if existing_user:
            return self.GenerateResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="User with this email already exists."
            )
        user_id=str(uuid.uuid4())
        new_user = User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            role=user_data.role,
            hashed_password=hash_password(user_data.password)
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})

        return self.GenerateResponse(
            status_code=status.HTTP_201_CREATED,
            message="User created successfully.",
            data={
                "user_id": new_user.id,
                "username": new_user.username,
                "role": new_user.role,
                "access_token": access_token,
                "refresh_token": refresh_token,
                }
        )

    def login_user(self, user_data: UserLogin):
        user = self.db.query(User).filter_by(email=user_data.email).first()
        if not user or not verify_password(user_data.password, user.hashed_password):
            return self.GenerateResponse(
                status_code = status.HTTP_401_UNAUTHORIZED,
                message="Invalid email or password."
            )
        
        user_id = str(user.id)
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})
        data = {
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

        return self.GenerateResponse(
            status_code=status.HTTP_200_OK,
            message="Login successful.",
            data=data
        )

    def update_profile(
        self, 
        user_data: ProfileModel, 
        token: str, 
        db: Session, 
        avi_file: Optional[UploadFile] = None
    ):
        current_user = self.get_current_user(token=token, db=db)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found!"
            )

        current_user.username = user_data.username or current_user.username
        current_user.full_name = user_data.full_name or current_user.full_name

        if avi_file:
            ext = avi_file.filename.split(".")[-1]
            file_name = f"{uuid4()}.{ext}"
            upload_dir = os.path.join(settings.MEDIA_DIR, "avi")
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, file_name)

            avi_file.file.seek(0) 
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(avi_file.file, buffer)

            current_user.avi = f"/static/avi/{file_name}"

        self.db.commit()
        self.db.refresh(current_user)

        # ✅ Return exactly what ProfileResponseWrapper expects
        return self.GenerateResponse(
                status_code=status.HTTP_200_OK,
                message="Profile updated successfully.",
                data=ProfileResponse.model_validate(current_user)
            )


    def logout_user(self, token: str, db: Session):
        current_user = self.get_current_user(token=token, db=db)

        # Check if already blacklisted
        if db.query(BlacklistedToken).filter_by(token=token).first():
            return self.GenerateResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Token has already been blacklisted."
            )

        # Blacklist the token
        try:
            db.add(BlacklistedToken(token=token))
            db.commit()
            return self.GenerateResponse(
                status_code=status.HTTP_200_OK,
                message="Logout successful."
            )
        except Exception as e:
            db.rollback()
            return self.GenerateResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Error logging out: {str(e)}"
            )

class TokenService:
    def __init__(self, db: Session):
        self.db = db

    def GenerateResponse(self, status_code:int, message:str, data:Optional[dict] = None):
        return JSONResponse(
            status_code=status_code,
            content={
                "message": message,
                "data": data
            }
        )
    def refresh_token(self, refresh_token: str):
        if is_token_blacklisted(self.db, refresh_token):
            return self.GenerateResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Token revoked!!"
            )
        try:
            payload = decode_refresh_token(refresh_token, self.db)
            user_id = payload.get("sub")
            
            blacklist_token(self.db, refresh_token)
            new_access_token = create_access_token({"sub": user_id})
            new_refresh_token = create_refresh_token({"sub": user_id})
            return self.GenerateResponse(
                status_code=status.HTTP_200_OK,
                message="New Access token generated!!",
                data={
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer"
                }
            )
        except Exception as e:
            print(f"Error decoding token: {e}")  # For debugging
            return self.GenerateResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message=f"Invalid token: {str(e)}"
            )