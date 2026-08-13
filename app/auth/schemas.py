from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    email: EmailStr

    phone_number: str | None = Field(
        default=None,
        max_length=20
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=72
    )


class UserLogin(BaseModel):
    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=72
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone_number: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True