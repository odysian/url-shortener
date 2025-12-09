from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import auth
import db_models
from db_config import get_db

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_session: Session = Depends(get_db),
) -> db_models.User:
    """
    Dependency to get the current authenticated user.

    Validates JWT token and returns User object.
    Raises 401 if token is invalid or user doesn't exist.

    Usage in routes:
        def my_route(current_user: User = Depends(get_current_user)):
            # current_user is automatically populated
    """
    token = credentials.credentials
    username = auth.decode_access_token(token)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = (
        db_session.query(db_models.User)
        .filter(db_models.User.username == username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user
