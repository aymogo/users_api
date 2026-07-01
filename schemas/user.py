from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.user import UserRole


class UserCreate(BaseModel):
    """Input schema for user registration."""

    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongPass123!"])
    first_name: str | None = Field(default=None, max_length=100, examples=["John"])
    last_name: str | None = Field(default=None, max_length=100, examples=["Doe"])


class UserUpdate(BaseModel):
    """Input schema for partial user update (PATCH). All fields optional."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    # Only an admin-authorized flow should allow role changes; kept here for
    # simplicity, but service layer enforces who is allowed to set it.
    role: UserRole | None = None


class UserResponse(BaseModel):
    """Output schema - never exposes hashed_password or verification codes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str | None
    last_name: str | None
    role: UserRole
    is_verified: bool
    created_at: datetime
    updated_at: datetime