from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    DATABASE_URL: str
    MEDIA_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    MOMENT_MEDIA_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()