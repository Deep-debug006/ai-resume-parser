"""
Authentication API Routes (Phase 18).
Implements JWT-based registration, login, and profile fetching.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.resume_models import UserModel
from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.services.auth_service import auth_service
from backend.app.core.auth_dependency import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with hashed password and returns a JWT access token.",
)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Registers user, hashes password with bcrypt, and issues JWT access token.
    Never exposes password hash.
    """
    try:
        user = auth_service.register_user(
            db=db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error("Failed to register user: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete user registration.",
        )

    # Issue JWT access token
    access_token = auth_service.create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=auth_service.to_user_response(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates user credentials and issues a JWT access token.",
)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Verifies user email and password against stored bcrypt hash.
    Raises 401 if invalid credentials.
    """
    user = auth_service.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT access token
    access_token = auth_service.create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=auth_service.to_user_response(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Returns the profile of the currently authenticated user. Requires valid Bearer JWT.",
)
def get_me(current_user: UserModel = Depends(get_current_user)) -> UserResponse:
    """
    Protected endpoint returning current user details without exposing password hashes.
    """
    return auth_service.to_user_response(current_user)
