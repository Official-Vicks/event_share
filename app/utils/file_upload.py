import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", ".gif", ".mp4", ".mov", ".avi"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def save_file(file: UploadFile, upload_dir: str, base_url: str = None):
    ext = file.filename.split(".")[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported media file type.\nMedia type must be image or short video")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    os.makedirs(upload_dir, exist_ok=True)

    file_name = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_dir, file_name)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if base_url:
        return f"{base_url}static/{os.path.basename(upload_dir)}/{file_name}"

    return f"/static/{os.path.basename(upload_dir)}/{file_name}"