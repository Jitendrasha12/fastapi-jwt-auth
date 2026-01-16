from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
import models, schemas, crud
from database import engine, get_db
from auth import create_access_token, get_current_user, require_role
from typing import List

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.authenticate_user(db, user.email, user.password)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "sub": str(db_user.id),
        "role": db_user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/signup", response_model=schemas.UserResponse)
def signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user_data = schemas.UserCreate(
        username=username,
        email=email,
        password=password
    )

    try:
        return crud.create_user(db, user_data, file)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )


@app.get("/profile", response_model=schemas.UserResponse)
def profile(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/posts", response_model=schemas.PostResponse)
def create_post(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=current_user.id
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return db_post

@app.get("/get-user-posts", response_model=List[schemas.PostResponse])
def get_post(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
    ):
    # Fix: Use the crud module correctly
    posts = crud.get_user_posts(db, current_user.id)
    return posts


@app.get("/admin")
def admin_dashboard(
    admin: models.User = Depends(require_role("admin"))
):
    return {"msg": f"Welcome Admin {admin.username}"}


@app.get("/user")
def user_dashboard(
    user: models.User = Depends(require_role("user"))
):
    return {"msg": f"Welcome User {user.username}"}

@app.get("/posts")
def get_posts(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit

    total = db.query(models.Post).count()

    posts = db.query(models.Post)\
        .offset(offset)\
        .limit(limit)\
        .all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": posts
    }


@app.get("/search-posts")
def search_posts(
    q: str,
    db: Session = Depends(get_db)
):
    posts = db.query(models.Post).filter(
        models.Post.title.ilike(f"%{q}%")
    ).all()

    return posts
#GET /search-posts?q=fastapi



@app.get("/my-posts")
def my_posts(
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    offset = (page - 1) * limit

    posts = db.query(models.Post)\
        .filter(models.Post.user_id == current_user.id)\
        .offset(offset)\
        .limit(limit)\
        .all()

    return posts


@app.get("/latest-posts")
def get_latest_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post)\
        .order_by(desc(models.Post.created_at))\
        .all()

    return posts

