"""
Authentication Service Layer (Phase 18).
Handles password hashing (bcrypt), JWT generation/verification, and user operations.
Never stores plaintext passwords or exposes password hashes.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.resume_models import UserModel
from backend.app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """
    Centralized service for authentication, password hashing, and JWT tokens.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes plaintext password using bcrypt with random salt.
        Never stores plaintext passwords.
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_bytes.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies plaintext password against stored bcrypt hash.
        """
        if not hashed_password:
            return False
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception as e:
            logger.warning("Error verifying password hash: %s", e)
            return False

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Creates a signed JWT access token.
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "iat": now,
            "exp": expire,
        })
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes and verifies a JWT token. Returns payload dict or None if invalid/expired.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.PyJWTError as e:
            logger.debug("JWT decode failure: %s", e)
            return None

    def register_user(
        self,
        db: Session,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> UserModel:
        """
        Registers a new user with hashed password.
        Raises ValueError if email is already registered.
        """
        clean_email = email.strip().lower()
        existing = db.query(UserModel).filter(UserModel.email == clean_email).first()
        if existing:
            raise ValueError(f"User with email '{clean_email}' already exists.")

        hashed = self.hash_password(password)
        user = UserModel(
            email=clean_email,
            full_name=full_name.strip() if full_name else None,
            hashed_password=hashed,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Successfully registered new user: id='%s', email='%s'", user.id, user.email)
        return user

    def authenticate_user(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> Optional[UserModel]:
        """
        Authenticates a user by email and password.
        Returns UserModel if valid, None otherwise.
        """
        clean_email = email.strip().lower()
        user = db.query(UserModel).filter(UserModel.email == clean_email).first()
        if not user or not user.hashed_password:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[UserModel]:
        """Retrieves user by primary key ID."""
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[UserModel]:
        """Retrieves user by email."""
        return db.query(UserModel).filter(UserModel.email == email.strip().lower()).first()

    @staticmethod
    def to_user_response(user: UserModel) -> UserResponse:
        """
        Converts UserModel into UserResponse. Never includes password hash.
        """
        return UserResponse(
            id=str(user.id),
            email=str(user.email),
            full_name=user.full_name,
            is_active=bool(user.is_active),
            created_at=user.created_at.isoformat() if user.created_at else None,
        )


auth_service = AuthService()
