from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.database.repositories import UserRepository
from app.utils.security import create_access_token, decode_access_token, verify_password

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SwitchUserRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=70)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True


class UserSummaryResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository.get_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    clean_name = (payload.full_name or "").strip()
    existing = UserRepository.get_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = UserRepository.create(
        db=db,
        email=payload.email,
        password=payload.password,
        full_name=clean_name if clean_name else None,
    )
    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = UserRepository.get_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }


@router.post("/switch-user", response_model=TokenResponse)
def switch_user(payload: SwitchUserRequest, db: Session = Depends(get_db)):
    """Switches active session to an existing or initial user account."""
    user = UserRepository.get_by_email(db, payload.email)
    if not user:
        clean_name = (payload.full_name or "").strip()
        user = UserRepository.create(
            db=db,
            email=payload.email,
            password="Password123!",
            full_name=clean_name if clean_name else None,
        )
    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }


@router.get("/users", response_model=List[UserSummaryResponse])
def list_users(db: Session = Depends(get_db)):
    """Lists available users for demo switcher and testing."""
    users = db.query(User).filter(User.is_active == True).order_by(User.created_at.asc()).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in users]


@router.get("/me", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": bool(current_user.is_admin),
        "is_active": bool(current_user.is_active),
    }


@router.get("/profile", response_model=UserProfileResponse)
def get_profile_alias(current_user: User = Depends(get_current_user)):
    """Alias for /me to satisfy RESTful profile convention."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": bool(current_user.is_admin),
        "is_active": bool(current_user.is_active),
    }


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clean_name = payload.full_name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name cannot be empty or whitespace only",
        )

    user = UserRepository.update_full_name(db, current_user.id, clean_name)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": bool(user.is_admin),
        "is_active": bool(user.is_active),
    }

