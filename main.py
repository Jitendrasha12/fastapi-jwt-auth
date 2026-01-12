from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, crud
from database import engine, get_db,SessionLocal
from auth import create_access_token,get_current_user


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.authenticate_user(db, user.email, user.password)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {"sub": str(db_user.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)



    from auth import get_current_user

@app.get("/profile")
def profile(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }
