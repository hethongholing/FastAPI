from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
import os
import shutil

router = APIRouter(tags=["User"])

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads")

@router.post("/users/{username}/avatar")
def upload_avatar(username: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    file_extension = os.path.splitext(file.filename)[1]
    filename = f"user_{username}{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.avatar = f"uploads/{filename}"
    db.commit()

    return {"message": "Upload thành công", "avatar": user.avatar}


@router.get("/users/{username}/avatar")
def get_avatar(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", user.avatar)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
