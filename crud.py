from sqlalchemy.orm import Session
import models
import schemas
from auth import hash_password, verify_password
from fastapi import UploadFile
import shutil
import uuid
import os

def create_user(db: Session, user: schemas.UserCreate, file: UploadFile):
    # Create the uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Generate a unique filename using UUID
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = f"uploads/{unique_filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_user = models.User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        profile_image=file_path
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def get_user_posts(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        return None
    
    return user.posts
