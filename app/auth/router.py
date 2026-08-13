from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user,
    require_roles,
)
from app.auth.roles import ADMIN, CUSTOMER
from app.auth.schemas import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password_hash=hash_password(user_data.password),
        role=CUSTOMER,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------

@router.get(
    "/profile",
    response_model=UserResponse,
)
def get_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


# ---------------------------------------------------------
# CUSTOMER-ONLY AREA
# ---------------------------------------------------------

@router.get(
    "/customer-area",
    response_model=UserResponse,
)
def customer_area(
    current_user: User = Depends(
        require_roles(CUSTOMER)
    ),
):
    return current_user


# ---------------------------------------------------------
# ADMIN-ONLY AREA
# ---------------------------------------------------------

@router.get(
    "/admin-area",
    response_model=UserResponse,
)
def admin_area(
    current_user: User = Depends(
        require_roles(ADMIN)
    ),
):
    return current_user