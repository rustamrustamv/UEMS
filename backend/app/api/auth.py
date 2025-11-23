"""
Authentication endpoints: login, register, token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.core.auth import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user
)
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserResponse, LoginRequest, LoginResponse,
    TokenRefreshRequest, TokenResponse
)
from app.instrumentation.metrics import (
    user_logins_total, user_login_failures_total, active_users_gauge
)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning(
            "Registration failed - email already exists",
            extra={'event': 'registration_failed', 'email': user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate role
    if user_data.role not in [role.value for role in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}"
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=UserRole(user_data.role),
        student_id=user_data.student_id,
        department=user_data.department,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Update metrics
    active_users_gauge.labels(role=new_user.role.value).inc()

    logger.info(
        "User registered successfully",
        extra={
            'event': 'user_registered',
            'user_id': str(new_user.id),
            'role': new_user.role.value,
            'email': new_user.email
        }
    )

    return new_user


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login and receive JWT tokens.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(credentials.password, user.password_hash):
        user_login_failures_total.labels(reason='invalid_credentials').inc()
        logger.warning(
            "Login failed - invalid credentials",
            extra={'event': 'login_failed', 'email': credentials.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is active
    if not user.is_active:
        user_login_failures_total.labels(reason='account_inactive').inc()
        logger.warning(
            "Login failed - account inactive",
            extra={'event': 'login_failed', 'user_id': str(user.id)}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Create tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "full_name": user.full_name
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Update metrics
    user_logins_total.labels(role=user.role.value).inc()

    logger.info(
        "User logged in successfully",
        extra={
            'event': 'user_login',
            'user_id': str(user.id),
            'role': user.role.value
        }
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(token_request.refresh_token)

    # Validate token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "full_name": user.full_name
    }
    access_token = create_access_token(token_data)

    logger.info(
        "Token refreshed",
        extra={'event': 'token_refreshed', 'user_id': str(user.id)}
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout (client should discard tokens).
    Note: JWT tokens are stateless, so we can't invalidate them server-side
    without a token blacklist (not implemented in this version).
    """
    # Optionally decrement active users gauge (requires token tracking)
    # For now, this is handled by periodic sync

    logger.info(
        "User logged out",
        extra={'event': 'user_logout', 'user_id': str(current_user.id)}
    )

    return {"message": "Logged out successfully"}
