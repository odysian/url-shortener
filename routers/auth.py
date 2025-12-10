"""
Authentication endpoints: register and login.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import auth
import db_models
import models
from db_config import get_db, settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED
)
def register_user(user_data: models.UserCreate, db_session: Session = Depends(get_db)):
    """
    Register a new user account.

    Checks for username/email conflicts before creating.
    Returns user data (no password).
    """
    # Check if username exists
    existing_user = (
        db_session.query(db_models.User)
        .filter(db_models.User.username == user_data.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    # Check if email exists
    existing_email = (
        db_session.query(db_models.User)
        .filter(db_models.User.email == user_data.email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    new_user = db_models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=auth.hash_password(user_data.password),
    )

    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)

    return new_user


@router.post("/login", response_model=models.Token)
def login_user(user_data: models.UserLogin, db_session: Session = Depends(get_db)):
    """
    Login with username and password.

    Returns JWT token for authentication.
    """
    # Find user
    user = (
        db_session.query(db_models.User)
        .filter(db_models.User.username == user_data.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not auth.verify_password(user_data.password, user.hashed_password):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create token
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return {"access_token": access_token, "token_type": "bearer"}
