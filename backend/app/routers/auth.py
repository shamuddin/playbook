"""Authentication endpoints for login, registration, and token management."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from app.database import get_db
from app.models import User, UserRole, utc_now
from app.schemas import StandardResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


@router.post("/login", response_model=StandardResponse)
async def login(
    credentials: dict,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Authenticate user and return JWT token."""
    email = credentials.get("email", "").lower().strip()
    password = credentials.get("password", "")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    user.last_login = utc_now()
    await db.commit()

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value},
        expires_delta=timedelta(hours=settings.access_token_expire_minutes / 60),
    )

    return StandardResponse(
        success=True,
        data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
            },
        },
    )


@router.post("/register", response_model=StandardResponse)
async def register(
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Register a new user account."""
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    full_name = data.get("full_name")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=UserRole.VIEWER,
    )
    db.add(user)
    await db.commit()

    return StandardResponse(
        success=True,
        data={"user_id": user.id, "email": user.email},
        message="User registered successfully",
    )


@router.get("/me", response_model=StandardResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> StandardResponse:
    """Get current authenticated user profile."""
    return StandardResponse(
        success=True,
        data={
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
        },
    )
